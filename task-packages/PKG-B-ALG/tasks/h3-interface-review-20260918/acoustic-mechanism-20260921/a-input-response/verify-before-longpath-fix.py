import hashlib,json,pathlib,subprocess
root=pathlib.Path.cwd();base='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/';pkg=root/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918';out=pathlib.Path(__file__).resolve().parent
h=lambda b:hashlib.sha256(b).hexdigest()
checks=[]
for commit,rel in [('df4b756ba49a2d161c03869a0a4a28034dad15b0','batches/c-adapter-first-20260913/GEOMETRY.md'),*[( '88805ee415f137998b59b7cb197f2eeb988d17b7',p) for p in ['continuous-prototype-01/delivery-01/evidence/simulation/four_mic_top.v','continuous-prototype-01/delivery-01/evidence/simulation/pdm_cic3.v','continuous-prototype-01/RESULTS.md']]]:
 path=base+rel;blob=subprocess.check_output(['git','show',commit+':'+path]);current=(root/path).read_bytes();checks.append(dict(path=path,commit=commit,git_blob_sha256=h(blob),working_sha256=h(current),bytes_equal=blob==current));assert blob==current,path
summary=json.loads((pkg/'checkpoint-20260923/evidence/run01/summary.json').read_text());bindings=[]
for rel,expected in summary['pins'].items():
 if not rel.endswith('/metadata.json'):continue
 p=root/rel;assert h(p.read_bytes())==expected
 binding=p.parent.parent/'version-binding.json';data=json.loads(binding.read_text());host=data['host_files'];bit=[v for k,v in host.items() if k.endswith('.bit')];elf=[v for k,v in host.items() if k.endswith('.elf')]
 assert bit==['b15991bc0f8595970361be553b542e334dbb7dca268c01864ecd80fcffbbffaf'];assert elf==['4b7823bdefa3776a910a3359b5851fa52c6f4ce89432cc3ee0072dee52ca06a6']
 blob=subprocess.check_output(['git','show','94b5fe79d87e038e895878fb31030cded469bb33:'+binding.relative_to(root).as_posix()]);assert blob==binding.read_bytes()
 bindings.append(dict(path=binding.relative_to(root).as_posix(),sha256=h(blob),bit=bit[0],elf=elf[0],scope='host binding, not FPGA readback'))
wav=root/(base+'batches/trusted-direction-input-20260918/playback-v1/soundsight-target-v1.wav');digest=h(wav.read_bytes());assert digest=='ce28c5576eea620d8f358c0799bf8029cdc41bdeae8dcf95a02967d3bace6838'
result=dict(status='B_READ_ONLY_CORROBORATION_NOT_CALIBRATION',version_checks=checks,bindings=bindings,host_wav_sha256=digest)
print(json.dumps(result,indent=2))
