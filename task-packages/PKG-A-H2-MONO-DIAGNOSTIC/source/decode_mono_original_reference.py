"""Decode a real DDR dump. Refuses wrong length/checksum/ID/sign/flags."""
import argparse, csv, json, struct, uuid
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument("binary",type=Path)
p.add_argument("--fnv",required=True,help="fnv1a32 printed by the board, hexadecimal")
p.add_argument("--output",required=True,type=Path)
a=p.parse_args()
raw=a.binary.read_bytes()
if len(raw)!=768000:raise ValueError("Expected exactly 768000 bytes")
h=2166136261
for v in raw:h=((h^v)*16777619)&0xffffffff
if h!=int(a.fnv,16):raise ValueError("DDR dump checksum does not match board")
rows=[]
for lo,hi,v,flags in struct.iter_unpack("<IIiI",raw):
 sid=(hi<<32)|lo
 if not -8388608<=v<=8388607:raise ValueError("PCM not sign-extended signed24")
 if flags&~2:raise ValueError("Unknown/error flags; reject clean export")
 if rows and sid!=rows[-1][0]+1:raise ValueError("Original sample ID discontinuity")
 rows.append((sid,v,flags))
# This is explicitly mono, NOT ss-data-draft-0.3 four-channel H1.
a.output.mkdir(parents=True,exist_ok=False)
with (a.output/"samples.csv").open("w",encoding="utf-8",newline="") as f:
 w=csv.writer(f,lineterminator="\n")
 w.writerow(["sample_id","pcm","flags"])
 w.writerows(rows)
meta={
 "schema_version":"ss-mono-diagnostic-0.1",
 "acquisition_id":str(uuid.uuid4()),"source_kind":"hardware-audio",
 "evidence_level":"diagnostic","channel_count":1,"channel_order":["mic0"],
 "sample_rate_hz":48000,"sample_rate_status":"configured; physical clock measurement pending",
 "pdm_clock_hz":3072000,"decimation":64,"filter":"CIC3 R64 M1 diagnostic only",
 "sample_format":{"encoding":"signed-pcm","storage_dtype":"int32","valid_bits":24,"alignment":"right","fractional_bits":0},
 "scaling":"PDM 0=-1,1=+1; CIC gain262144; multiply32; saturate signed24",
 "warmup_discard_samples":4096,"warmup_duration_s":4096/48000,
 "id_origin":"PCM outputs since frontend reset; warmup/idle IDs not renumbered",
 "flags":{"1":"reserved overflow; rejected","2":"PCM output saturation"},
 "sample_count":len(rows),"binary_byte_order":"little",
 "capture_point":"PS DDR after DMA S2MM and cache invalidation; post-capture JTAG dump",
 "fnv1a32":f"{h:08x}","calibration_status":"not-calibrated",
 "acoustic_acceptance":False,
 "statistics":{"min":min(r[1] for r in rows),"max":max(r[1] for r in rows),
 "zero_count":sum(r[1]==0 for r in rows),"clipped_count":sum(bool(r[2]&2) for r in rows)},
 "limitations":["Not four-channel H1/H2 acceptance.","CIC has passband droop and limited anti-alias attenuation; no compensation FIR.",
 "24-bit container does not imply 24 effective acoustic bits.","Clock/pin timing and physical microphone behavior require board evidence."]
}
(a.output/"metadata.json").write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8")
print("MONO_DECODE_PASS samples=48000 checksum/IDs/sign/flags checked")
