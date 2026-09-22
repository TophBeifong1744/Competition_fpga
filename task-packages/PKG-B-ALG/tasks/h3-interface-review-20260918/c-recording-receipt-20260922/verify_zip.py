"""Read-only ZIP receipt: reuse approved S1 verifier; no metadata fabrication."""
import argparse,hashlib,importlib.util,json,pathlib,platform,sys,zipfile
import numpy as np

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',type=pathlib.Path,required=True);ap.add_argument('--zip',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
 repo=a.repo.resolve();src=repo/'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/background-target-stop-20260917/finish_scene.py';spec=importlib.util.spec_from_file_location('approved_scene',src);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
 ziphash=sha(a.zip.read_bytes());results=[];manifest={};inventory=[]
 with zipfile.ZipFile(a.zip) as z:
  names=[i.filename for i in z.infolist()];assert len(names)==len(set(names)),'DUPLICATE_ZIP_PATH'
  for i in z.infolist():
   p=pathlib.PurePosixPath(i.filename);assert not p.is_absolute() and '..' not in p.parts and '\\' not in i.filename,'UNSAFE_ZIP_PATH'
   if not i.is_dir():manifest[i.filename]=sha(z.read(i));inventory.append(dict(path=i.filename,bytes=i.file_size,crc32=f'{i.CRC:08X}'))
  for path in sorted(n for n in names if n.endswith('.bin')):
   raw=z.read(path);logpath=path[:-4]+'.log';log=z.read(logpath).decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n');name=pathlib.PurePosixPath(path).stem
   r=dict(name=name,raw_sha256=manifest[path],log_sha256=manifest[logpath])
   try:
    checked=old.verify(raw,log);u=np.frombuffer(raw,'<u4').reshape(-1,8);pcm=u[:,2:6].view('<i4');x=pcm.astype(np.float64);center=x-x.mean(axis=0)
    r.update(status='PASS_RAW_UART_ONLY',checked=checked,dc_codes=x.mean(axis=0).tolist(),ac_rms_codes=np.sqrt(np.mean(center*center,axis=0)).tolist(),constant_channels=[bool(np.all(pcm[:,k]==pcm[0,k])) for k in range(4)],identical_channel_pairs=[[i,j] for i in range(4) for j in range(i+1,4) if np.array_equal(pcm[:,i],pcm[:,j])],fullscale_code_counts=[int(np.count_nonzero((pcm[:,k]==-8388608)|(pcm[:,k]==8388607))) for k in range(4)],pcm_multiple32=bool(np.all(pcm%32==0)))
   except Exception as e:r.update(status='FAIL_RAW_UART',error=repr(e))
   results.append(r);print(name,r['status'],r.get('checked',{}).get('flagged_rows'),flush=True)
 assert sha(a.zip.read_bytes())==ziphash,'ZIP_CHANGED'
 dep=[src,repo/'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/source/export_four.py']
 out=dict(status='PARTIAL_RECEIPT_PENDING_POSITION_AND_PROVENANCE',zip_name=a.zip.name,zip_sha256=ziphash,zip_bytes=a.zip.stat().st_size,python=platform.python_version(),numpy=np.__version__,source_sha256=sha(pathlib.Path(__file__).read_bytes()),dependencies={p.relative_to(repo).as_posix():sha(p.read_bytes()) for p in dep},inventory=inventory,input_sha256=manifest,captures=results,all_raw_unique=len({r['raw_sha256'] for r in results})==len(results),passed=sum(r['status']=='PASS_RAW_UART_ONLY' for r in results),missing=['capture-to-scene mapping (back_od, az045)','measured source positions and measurement method/uncertainty','position photos and fixation/orientation records','per-capture metadata/config/geometry identity','actual load bit/ELF binding and playback source identity','operator chronology and anomalies'],not_tested=['DOA/tracking','marker alignment and playback content','human listening','objective audio gain','physical acoustic mapping/calibration'])
 (a.out/'result.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 print(json.dumps({'passed':out['passed'],'captures':len(results),'unique':out['all_raw_unique'],'zip_sha256':ziphash}))
if __name__=='__main__':main()
