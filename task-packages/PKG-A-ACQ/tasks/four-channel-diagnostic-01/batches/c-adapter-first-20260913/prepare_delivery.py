"""Wrap existing exporters/readers; archive a new diagnostic delivery, never run hardware."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import traceback
import wave
import zipfile

ROOT = Path(__file__).resolve().parent
TASK = ROOT.parents[1]
REPO = TASK.parents[3]
SOURCE = TASK / 'source'
READER = REPO / 'task-packages/PKG-B-ALG/payload/model/python/h1_reader.py'
sys.path.insert(0, str(SOURCE))
from export_c_capture import verify
from export_four import decode


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New directory; never overwrite')
    parser.add_argument('--vitis-workspace', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT) or out == ROOT:
        parser.error('Output must be a new child directory of this batch')
    out.mkdir(exist_ok=False)
    commands = []

    def run(argv, label, cwd=REPO):
        commands.append({'argv': [str(x) for x in argv], 'cwd': str(cwd)})
        with (out/'logs'/f'{label}.log').open('x', encoding='utf-8') as log:
            p = subprocess.run([str(x) for x in argv], cwd=cwd, stdout=log,
                               stderr=subprocess.STDOUT, shell=False)
        commands[-1]['returncode'] = p.returncode
        if p.returncode:
            raise RuntimeError(f'{label} failed: {p.returncode}; preserve output')

    try:
        (out/'logs').mkdir()
        (out/'versions').mkdir()
        received = ROOT/'received-01'
        original_hashes = json.loads((received/'SHA256.json').read_text(encoding='utf-8'))
        for name, digest in original_hashes.items():
            if sha(received/name) != digest:
                raise ValueError(f'Received evidence changed: {name}')
        operator = json.loads((ROOT/'operator-record.json').read_text(encoding='utf-8'))
        if not all(operator['confirmed'].values()):
            raise ValueError('Operator declaration incomplete; do not assert confirmation')
        shutil.copyfile(ROOT/'operator-record.json', out/'operator-record.json')
        shutil.copyfile(received/'setup-original.jpg', out/'setup-original.jpg')
        shutil.copyfile(received/'check.json', out/'initial-integrity-and-audio-stats.json')
        app = args.vitis_workspace/'four_mic_capture'
        artifacts = {
            'system_c_adapter.bit': (app/'_ide/bitstream/system_c_adapter.bit', '37f6d55fbd1ce314245d189fbe2fa984477c6b61d26a2a23736b71305654605b'),
            'four_mic_capture.elf': (app/'build/four_mic_capture.elf', 'c0b430e77d4d0d53d4ca0b4399fe69e0cd7865e5815ac3549b5d209d39e7192a'),
            'ps7_init.tcl': (app/'_ide/psinit/ps7_init.tcl', 'a158fcc7d723b21003864159006e781ffaf5e8df24ec9b1d9279f9d14ff3ee5e'),
            'system_c_adapter.xsa': (args.vitis_workspace/'c_adapter_platform/export/c_adapter_platform/hw/system_c_adapter.xsa', '71e7bf6d4fcb769582e5485660515b8f615b2027aa2ff18c1f8d3f67f9457baa')
        }
        versions = {'scope': 'disk hashes plus user-confirmed Run use; not cryptographic FPGA readback', 'files': {}}
        for name, (path, expected) in artifacts.items():
            if sha(path) != expected:
                raise ValueError(f'Loading artifact differs from previously checked version: {path}')
            shutil.copyfile(path, out/'versions'/name)
            if sha(out/'versions'/name) != expected:
                raise ValueError('Snapshot mismatch')
            versions['files'][name] = {'path': str(path), 'sha256': expected, 'bytes': path.stat().st_size}
        for name, path in {'launch.json':app/'_ide/launch.json', 'main_four_capture.c':app/'src/main_four_capture.c',
                           'lscript.ld':app/'src/lscript.ld', 'memory.map':app/'build/memory.map'}.items():
            shutil.copyfile(path, out/'versions'/name)
            versions['files'][name] = {'path':str(path), 'sha256':sha(path), 'bytes':path.stat().st_size}
        with zipfile.ZipFile(out/'versions/system_c_adapter.xsa') as archive:
            bits = [n for n in archive.namelist() if n.endswith('.bit')]
            inits = [n for n in archive.namelist() if n.endswith('ps7_init.tcl')]
            if len(bits) != 1 or len(inits) != 1:
                raise ValueError('Ambiguous XSA contents')
            if hashlib.sha256(archive.read(bits[0])).hexdigest() != artifacts['system_c_adapter.bit'][1]:
                raise ValueError('XSA/bit mismatch')
            if hashlib.sha256(archive.read(inits[0])).hexdigest() != artifacts['ps7_init.tcl'][1]:
                raise ValueError('XSA/init mismatch')
        save(out/'versions/loading-record.json', versions)
        run([sys.executable, '-B', '-m', 'unittest', '-v', 'test_export', 'test_c_capture_gate'], 'exporter-tests', SOURCE)
        checks = {}
        for scene in ('quiet', 'speech'):
            rawpath = received/scene/'raw.bin'
            serialpath = received/scene/'serial.log'
            directory = out/f'c-adapter-{scene}-20260913-01'
            acquisition = directory.name
            run([sys.executable, '-B', SOURCE/'export_c_capture.py', rawpath, serialpath, directory,
                 '--acquisition-id', acquisition, '--operator', 'Toph Beifong',
                 '--scene', 'Quiet background' if scene == 'quiet' else 'Audible source active before Run; user-described placement in operator-record.json',
                 '--numbered-mating-confirmed'], f'export-{scene}')
            # Preserve the original exporter output before adding this batch's new geometry.
            shutil.copyfile(directory/'metadata.json', out/'logs'/f'{scene}-exporter-original-metadata.json')
            meta = json.loads((directory/'metadata.json').read_text(encoding='utf-8'))
            meta['firmware_config_version'] = meta['config_version']
            meta['config_version'] = 'four-channel-c-adapter-v1-usergeom-20260913-v1'
            meta['geometry_version'] = operator['geometry']['geometry_version']
            meta['coordinates_m'] = operator['geometry']['coordinates_m']
            meta['geometry_record'] = operator['geometry']
            meta['operator_confirmation'] = operator['confirmed']
            meta['source_placement_estimate'] = operator['speech_source'] if scene == 'speech' else None
            meta['provisional_fields']['coordinates_m'] = 'Derived from user-measured 40 mm edges and user-confirmed planar square; method, tolerance and diagonals not supplied; not precision-calibrated.'
            meta['provisional_fields']['channel_order'] = 'User photo labels and confirmed numbered wiring; no independent per-microphone acoustic mapping test.'
            meta['adapter_interface']['geometry'] = 'See geometry_record: user-reported measurement and declared square; original design-only unmeasured note superseded for this dataset.'
            meta['config_version_note'] = 'New H1 full configuration label required by added physical geometry; runtime firmware, packet layout and PCM are unchanged.'
            meta['loading_record'] = '../versions/loading-record.json'
            (directory/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            raw = rawpath.read_bytes()
            fnv = verify(raw, serialpath.read_text(encoding='utf-8-sig'))
            decoded = decode(raw)
            with (directory/'samples.csv').open(encoding='utf-8',newline='') as stream:
                csvrows = list(csv.reader(stream))
            if [[str(v) for v in r] for r in decoded] != csvrows[1:]:
                raise ValueError('CSV does not exactly preserve decoded values and error flags')
            if (directory/'raw.bin').read_bytes() != raw or sha(directory/'serial.log') != sha(serialpath):
                raise ValueError('Original copy differs')
            wavs = []
            for ch in range(4):
                shutil.copyfile(received/scene/f'mic{ch}.wav',directory/f'mic{ch}.wav')
                with wave.open(str(directory/f'mic{ch}.wav'),'rb') as wav:
                    if (wav.getnchannels(),wav.getsampwidth(),wav.getframerate(),wav.getnframes()) != (1,2,48000,32000):
                        raise ValueError('Unexpected WAV format')
                    pcm = list(struct.unpack('<32000h',wav.readframes(32000)))
                expected = [round(r[ch+1]*12/256) for r in decoded]
                if pcm != expected:
                    raise ValueError('WAV derivative mismatch')
                wavs.append({'channel':ch,'sha256':sha(directory/f'mic{ch}.wav'),'additional_clipping':0})
            save(directory/'listening.json', {'common_gain':12, 'formula':'round(PCM24*12/256)',
                'processing':'listening copy only; no filtering or per-channel normalization', 'files':wavs})
            checks[scene] = {'groups':len(decoded),'bytes':len(raw),'fnv1a32':f'{fnv:08X}',
                'first_id':decoded[0][0],'last_id':decoded[-1][0], 'error_rows':sum(r[5] for r in decoded),
                'all_seven_csv_columns_equal_decoded_bin':True, 'raw_and_serial_unchanged':True}
        directories = [out/f'c-adapter-{s}-20260913-01' for s in ('quiet','speech')]
        run([sys.executable, '-B', READER, *directories], 'h1-reader')
        run([sys.executable, '-B', READER, TASK/'captures/dupont-quiet-01', TASK/'captures/dupont-speech-01', *directories], 'h1-historical-coexistence')
        if any(sha(received/name) != digest for name,digest in original_hashes.items()):
            raise ValueError('Received evidence changed during export')
        deps = [Path(__file__), ROOT/'operator-record.json', SOURCE/'export_four.py', SOURCE/'export_c_capture.py',
                SOURCE/'c_adapter_mapping.json', SOURCE/'test_export.py', SOURCE/'test_c_capture_gate.py', READER,
                REPO/'docs/minimal-data-interface.md']
        save(out/'dependencies.json', {p.relative_to(REPO).as_posix():sha(p) for p in deps})
        save(out/'RESULT.json', {'status':'PASS_OFFLINE_DELIVERY_CHECKS_NOT_B_ACCEPTANCE',
             'created_utc':datetime.now(timezone.utc).isoformat(), 'captures':checks,
             'hardware_build_this_run':False, 'agent_board_operation':False,
             'operator_audio_feedback':'User reports audible clear sound; not assistant listening judgment',
             'geometry':'User-measured sides plus declared coplanar square; method/uncertainty unknown',
             'h1_reader':'PASS_FORMAT_ONLY', 'independent_B_review':'pending', 'formal_M1':'not_claimed'})
    except Exception:
        (out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise
    finally:
        save(out/'commands.json', commands)
        save(out/'SHA256.json', {p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file()})
    print('PASS_OFFLINE_DELIVERY_CHECKS_NOT_B_ACCEPTANCE', out)


if __name__ == '__main__':
    main()
