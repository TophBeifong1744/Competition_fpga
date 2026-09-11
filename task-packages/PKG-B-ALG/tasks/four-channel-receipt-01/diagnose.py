"""H1 four-channel receipt diagnostics using the existing strict reader."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
READER_PATH = HERE.parents[1] / 'payload/model/python/h1_reader.py'
spec = importlib.util.spec_from_file_location('receipt_existing_h1_reader', READER_PATH)
reader = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = reader
spec.loader.exec_module(reader)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def amplitude(samples):
    """PCM float conversion is for statistics only; IDs never enter floats."""
    if len(samples) == 0:
        return []
    output = []
    for index, name in enumerate(reader.CHANNELS):
        codes = samples[:, index]
        values = codes.astype(np.float64)
        mean = float(values.mean())
        output.append(dict(channel=name, samples=len(values), minimum=int(codes.min()),
            maximum=int(codes.max()), mean_pcm=mean, rms_pcm=float(np.sqrt(np.mean(values*values))),
            ac_rms_pcm=float(np.sqrt(np.mean((values-mean)**2))),
            peak_fullscale=float(np.max(np.abs(values))/2**23),
            full_scale_code_count=int(np.count_nonzero((codes == -2**23) | (codes == 2**23-1))),
            zero_code_count=int(np.count_nonzero(codes == 0)),
            constant=bool(np.all(codes == codes[0]))))
    return output

def observations(recording, correlation_threshold, min_pair_samples):
    """Pair hints are calculated within each clean interval, never over gaps."""
    findings, pairs = [], []
    clean = recording.samples[recording.stream_error == 0]
    for item in amplitude(clean):
        if item['constant']:
            findings.append(dict(code='CONSTANT_CLEAN_CHANNEL', channel=item['channel'],
                message='格式无错行中码值恒定；可能是码型、静音或通道异常，需核对来源。'))
    for region in recording.clean_intervals:
        start, stop = region['row_start'], region['row_stop']
        data = recording.samples[start:stop].astype(np.float64)
        if len(data) < min_pair_samples:
            continue
        for a in range(4):
            for b in range(a+1, 4):
                x, y = data[:, a], data[:, b]
                xc, yc = x-x.mean(), y-y.mean()
                nx, ny = float(np.linalg.norm(xc)), float(np.linalg.norm(yc))
                corr = float(np.clip(np.dot(xc/nx, yc/ny), -1, 1)) if nx and ny else None
                equal = bool(np.array_equal(x, y))
                inverted = bool(np.array_equal(x, -y)) and bool(np.any(x))
                item = dict(channels=[reader.CHANNELS[a], reader.CHANNELS[b]],
                    row_start=start, row_stop=stop, first_sample_id=str(region['first_sample_id']),
                    last_sample_id=str(region['last_sample_id']), samples=len(data),
                    exact_equal=equal, exact_inverted=inverted, pearson=corr)
                pairs.append(item)
                if equal or inverted or (corr is not None and abs(corr) >= correlation_threshold):
                    findings.append(dict(code='PAIR_SIMILARITY_HINT', **item,
                        message='可能与同源声音、码型、极性或复制通道有关；不能单凭相似度裁定同步/映射正确或造假。'))
    if not pairs:
        findings.append(dict(code='INSUFFICIENT_CLEAN_PAIR_SAMPLES',
            message=f'没有长度达到{min_pair_samples}的格式无错连续区间，相似度未评估。'))
    return findings, pairs

def diagnose(directory, session, correlation_threshold=.995, min_pair_samples=32):
    directory = Path(directory).resolve()
    recording = session.load(directory)
    clean = recording.samples[recording.stream_error == 0]
    stats = amplitude(recording.samples)
    hints, pairs = observations(recording, correlation_threshold, min_pair_samples)
    errors = [dict(row_index=i, csv_line=i+2, sample_id=str(int(recording.sample_ids[i])),
        pcm=recording.samples[i].tolist(), flags=list(flags))
        for i, flags in enumerate(recording.error_flags) if flags]
    counts = Counter(flag for flags in recording.error_flags for flag in flags)
    if errors:
        hints.append(dict(code='REPORTED_STREAM_ERRORS', message='错误行已保留；相关统计只使用格式无错连续区间。'))
    if any(item['full_scale_code_count'] for item in stats):
        hints.append(dict(code='FULL_SCALE_ENDPOINTS', message='存在满量程端点，需检查削顶；端点出现次数本身不是削顶结论。'))
    meta = recording.metadata
    if meta['source_kind'] != 'hardware-audio':
        hints.append(dict(code='NOT_REAL_AUDIO_RECEIPT', message='来源声明为码型或合成数据，不能记作真实四路H2。'))
    if meta['coordinates_m'] is None or meta['calibration_status'] != 'calibrated':
        hints.append(dict(code='GEOMETRY_OR_CALIBRATION_UNVERIFIED', message='可做通道诊断，不能据此宣称方向精度或SNR。'))
    base = recording.summary()
    # IDs in public output use strings so downstream JS cannot round uint64.
    for key in ('first_sample_id', 'last_sample_id'):
        base[key] = str(base[key])
    for region in base['clean_intervals']:
        for key in ('first_sample_id', 'last_sample_id'):
            region[key] = str(region[key])
    for gap in base['missing_intervals']:
        for key in ('first', 'last', 'count'):
            gap[key] = str(gap[key])
    base.update(directory=str(directory), parse_status='READABLE_FORMAT_ONLY',
        channel_count=recording.samples.shape[1], channel_order=meta['channel_order'],
        source_kind=meta['source_kind'], sample_rate_hz_declared=meta['sample_rate_hz'],
        sample_rate_measured_verified=False, provisional_fields=meta['provisional_fields'],
        nominal_duration_from_row_count_s=len(recording.samples)/meta['sample_rate_hz'],
        flagged_rows=errors, flag_row_counts=dict(counts),
        relock_flag_rows=counts.get('relock', 0), reset_events_verified=False,
        amplitude_all_rows=stats, amplitude_format_clean_rows=amplitude(clean),
        pair_intervals=pairs, observations=hints, h2_acceptance=False,
        next_action='先核查错误/可疑通道及来源；可解析不等于采集验收通过。',
        sample_id_output='decimal strings; original uint64 values retained',
        notes=['未排序、重编号、补样、滤波或改增益；文件之间不拼接。',
               '均值/RMS包括直流；AC RMS只减均值作统计，不产生处理后音频。',
               'relock标志行数不是已验证重启事件数；新acquisition由元数据声明。'])
    return base

def run(directories, out, correlation_threshold=.995, min_pair_samples=32):
    directories = [Path(p).resolve() for p in directories]
    out = Path(out).resolve()
    if not 0 < correlation_threshold <= 1 or min_pair_samples < 2:
        raise ValueError('invalid correlation diagnostic settings')
    if any(out == p or p in out.parents for p in directories):
        raise ValueError('output must be outside every input directory')
    out.mkdir(parents=True, exist_ok=False)
    session = reader.ReaderSession()
    segments, errors = [], []
    previous_acquisition = None
    for path in directories:
        try:
            report = diagnose(path, session, correlation_threshold, min_pair_samples)
            report['acquisition_change_from_previous_readable'] = (
                previous_acquisition is not None and previous_acquisition != report['acquisition_id'])
            previous_acquisition = report['acquisition_id']
            segments.append(report)
            errors.extend(dict(directory=str(path), severity='reported_stream_error', **row)
                          for row in report['flagged_rows'])
        except reader.DataError as exc:
            hashes = {name: sha(path/name) for name in ('metadata.json','samples.csv') if (path/name).is_file()}
            issue = dict(directory=str(path), severity='fatal_format_error', code=exc.code,
                field=exc.field, csv_line=exc.line, message=str(exc), file_sha256=hashes)
            errors.append(issue)
            segments.append(dict(directory=str(path), parse_status='REJECTED', error=issue,
                                 next_action='修订导出器或元数据并交新版本；原始文件保持不变。'))
    rejected = sum(s['parse_status'] == 'REJECTED' for s in segments)
    result = dict(status='PARTIAL_OR_REJECTED' if rejected else 'READABLE_DIAGNOSTIC_ONLY',
        input_directories=len(directories), readable=len(segments)-rejected, rejected=rejected,
        segments=segments, h2_acceptance=False, four_channel_real_input_verified=False,
        diagnostic_settings=dict(correlation_threshold=correlation_threshold,min_pair_samples=min_pair_samples),
        error_reporting='Each rejected recording stops at first strict-reader failure; no partial salvage. Other directories continue.',
        environment=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform()),
        sources={str(READER_PATH):sha(READER_PATH),str(Path(__file__)):sha(Path(__file__))})
    for filename, value in [('summary.json',result),('errors.json',errors)]:
        (out/filename).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    lines=['# 四路输入诊断回执', '', f'状态：{result["status"]}；可解析 {result["readable"]}，拒绝 {rejected}。',
           '', '仅文件与数值诊断；来源、物理映射、同步、采样率和声学效果未独立验收。', '']
    for s in segments:
        lines += [f'## {Path(s["directory"]).name}', '', f'输入：`{s["directory"]}`', '']
        if s['parse_status']=='REJECTED':
            e=s['error'];lines += [f'拒绝：{e["message"]}', '',s['next_action'],''];continue
        lines += [f'{s["channel_count"]}路，{s["samples"]}样本；ID {s["first_sample_id"]}–{s["last_sample_id"]}。',
                  f'配置 `{s["config_version"]}`；来源 `{s["source_kind"]}`；错误行 {len(s["flagged_rows"])}。','',
                  '| 通道 | 最小/最大码 | 均值 | RMS | 满量程端点数 |',
                  '|---|---:|---:|---:|---:|']
        for a in s['amplitude_all_rows']:
            lines.append(f'| {a["channel"]} | {a["minimum"]}/{a["maximum"]} | {a["mean_pcm"]:.4f} | {a["rms_pcm"]:.4f} | {a["full_scale_code_count"]} |')
        codes=sorted({h['code'] for h in s['observations']})
        lines += ['', '观察：'+(', '.join(codes) or '本入口未发现所检查的异常线索'), '', s['next_action'], '']
    lines += ['错误原行及位置见 errors.json；完整连续区间、每路统计、相关性及输入SHA见 summary.json。',
              '频繁相似度提示需要结合声源/码型解释，不能证明复制、同步或物理映射。']
    (out/'receipt.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories',nargs='+',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--correlation-threshold',type=float,default=.995)
    parser.add_argument('--min-pair-samples',type=int,default=32)
    args=parser.parse_args()
    try:
        result=run(args.directories,args.out,args.correlation_threshold,args.min_pair_samples)
    except (OSError,ValueError) as exc:
        print(str(exc),file=sys.stderr);return 2
    print(json.dumps({k:result[k] for k in ('status','readable','rejected','h2_acceptance')},ensure_ascii=False))
    return 2 if result['rejected'] else 0

if __name__=='__main__':raise SystemExit(main())
