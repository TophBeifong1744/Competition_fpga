"""Freeze finite contract-derived cases, without importing or running the DUT."""
import argparse, copy, hashlib, io, json, pathlib, struct, zipfile

SPEC='6931206cc7dc89f992913e8231a5c95604bcafb5e1a7faec1facf4a08329f5ed'
RAW='902fb37e4b7533c22c8b59d1c3b011f7820df3e5063ccff994b940496464cbc2'
ROLES={
 'result':('ss-b-saved-portable-result-v1','SAVED_RESULT_FIELDS','SELECTED_FRAME_PAIR'),
 'index':('ss-b-saved-run-index-v1','SAVED_RUN_LINKS','RUN_ASSOCIATION'),
 'config':('ss-b-research-config-v1','RESEARCH_CONFIG_FIELDS','RESEARCH_APPLICABILITY'),
 'zip':('ss-b-saved-ifft-npz-v1','SAVED_CONTAINER_BYTES','CONTAINER_VIEW'),
 'npy':('ss-b-saved-ifft-npy-v1','SAVED_MEMBER_LAYOUT','SELECTED_FRAME_PAIR'),
 'rule':('ss-b-lag-rule-source-v1','WHITELIST_RULE_BYTES','WHITELIST_GLOBAL_RULE')}
FACTS=('valid','reason','peak','delta_q12','tau_q12','peak_code','physical_limit_q12','pair_length_sq','separated_margin_q15')
def encode(x): return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def bind(b): return {'sha256':hashlib.sha256(b).hexdigest(),'byte_length':str(len(b))}
def save(p,x): p.write_bytes(encode(x))
def new_value(x):
    if type(x) is int: return str(x)
    if type(x) is dict: return {k:new_value(v) for k,v in x.items()}
    if type(x) is list: return [new_value(v) for v in x]
    return x
def unknown(): return {'state':'UNKNOWN','reason':'Not supplied by this bounded test'}
def basic():
    rows=[]
    for L,T,valid,reason in [(1,22928,False,'TAU_BOUND'),(2,32425,True,'VALID')]:
        rows.append(dict(peak=6,delta_q12=13,tau_q12=24589,peak_code=123,physical_limit_q12=T,pair_length_sq=L,valid=valid,reason=reason,separated_margin_q15=17))
    return {'stage_details':[{'units':{'lag_01':'OK','lag_02':'OK'},'detail':{
        'frame_identity':{'boot':'SYNTH_BOOT','session':'SYNTH_SESSION','interval':'SYNTH_INTERVAL','frame':0,'generation':0,'last_id':1023},
        'pair_rows':rows,'numeric_invalid':False,'invalid_reasons':[],'fft_flags':{},'fixed4':{},'fixed4_totals':{},'ifft_flags':{}}}],
        'events':[{'synthetic':'unchanged history'}]}
def archive(member,duplicate=False,stored=False):
    s=io.BytesIO()
    with zipfile.ZipFile(s,'w',compression=zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED) as z:
        z.writestr('frame0002_ifft_real.npy',member)
        if duplicate: z.writestr('frame0002_ifft_real.npy',member)
    return s.getvalue()

class Case:
    def __init__(self,root,name):
        self.p=root/name; self.p.mkdir(); self.name=name; self.sources=[]; self.expected_sources={}; self.entries=[]; self.views=[]
        self.expected={'case':name,'exit':0,'result':'INCOMPLETE','processed':[], 'facts':{},'identities':{},'units':{},'errors':[],
                       'sources':self.expected_sources,'checks':['EXIT','NO_ESCALATION','DENOMINATOR','FACTS','IDENTITY','SOURCE']}
    def source(self,sid,role,b,path=None,declared=None,member_parent=None):
        h=bind(b); decl=declared or h
        sch,dec,scope=ROLES[role]
        ref={'schema_id':sch,'schema_version':'1','schema_sha256':SPEC,'encoding':'RAW_BYTES','content_sha256':decl['sha256']}
        if member_parent:
            loc={'kind':'ZIP_MEMBER','container_id':member_parent,'member_name':'frame0002_ifft_real.npy'}
        else:
            p=self.p/(sid+'.bin')
            if path is None: p.write_bytes(b)
            loc={'kind':'FILE','path':str(path or p.resolve())}
        self.entries.append({'id':sid,'ref':ref,'byte_length':decl['byte_length'],'location':loc})
        self.sources.append((sid,role,b,ref,dec,scope,decl))
        return sid
    def view(self,sid,data=None,j=0,k=0,array=False):
        vid='view'+str(len(self.views))
        av={'state':'KNOWN','value':{'container_id':'z','member_id':'n','member_name':'frame0002_ifft_real.npy','row_ordinal':str(k)}} if array else unknown()
        self.views.append({'id':vid,'result_id':sid,'stage_ordinal':str(j),'pair_ordinal':str(k),'array_view':av,'context_id':unknown(),'support_ids':[]})
        self.expected['processed'].append(data is not None)
        if data is not None:
            stage=data['stage_details'][j]; detail=stage['detail']; row=detail['pair_rows'][k]
            self.expected['facts'][vid]={n:new_value(row[n]) for n in FACTS if n in row}
            self.expected['identities'][vid]=new_value(detail.get('frame_identity',{}))
            self.expected['units'][vid]=new_value(stage['units'])
            for unit,status in stage['units'].items():
                if status.startswith('ALGORITHM_REJECTED:'):
                    self.error(sid,f'/stage_details/{j}/units/{unit}',status)
            for n,reason in enumerate(detail.get('invalid_reasons',[])):
                self.error(sid,f'/stage_details/{j}/detail/invalid_reasons/{n}',reason)
        return vid
    def error(self,sid,loc,reason):
        e={'source_id':sid,'locator':loc,'text':reason,'utf8':len(reason.encode('utf-8'))}
        if e not in self.expected['errors']: self.expected['errors'].append(e)
    def freeze(self,mutate=None,budget=64<<20):
        reg={'schema_id':'ss-b-producer-registry-v1','schema_version':'1','proposal_state':'PROPOSED_NOT_ACTIVE','profile':'SAVED_RESEARCH_DIAGNOSTIC',
             'decoder_specification':{'sha256':SPEC,'byte_length':'24400'},'raw_specification':{'sha256':RAW,'byte_length':'12626'},'entries':[]}
        groups={}
        for sid,role,b,ref,dec,scope,decl in self.sources:
            key=tuple(ref[n] for n in ('schema_id','schema_version','schema_sha256','encoding'))
            if key not in groups:
                e={'id':'reg'+str(len(groups)),'source_schema':{n:ref[n] for n in ('schema_id','schema_version','schema_sha256','encoding')},'decoder_role':dec,'scope_rule':scope,'whitelist':[]}
                groups[key]=e;reg['entries'].append(e)
            if decl not in groups[key]['whitelist']: groups[key]['whitelist'].append(decl)
        am={'schema_id':'ss-b-producer-access-map-v1','schema_version':'1','proposal_state':'PROPOSED_NOT_ACTIVE','profile':'SAVED_RESEARCH_DIAGNOSTIC',
            'registry_binding':{},'read_budget_bytes':str(budget),'entries':self.entries}
        sel={'schema_id':'ss-b-producer-selection-v1','schema_version':'1','proposal_state':'PROPOSED_NOT_ACTIVE','profile':'SAVED_RESEARCH_DIAGNOSTIC',
             'registry_binding':{},'access_map_binding':{},'views':self.views}
        if mutate: mutate(reg,am,sel)
        rb=encode(reg); am['registry_binding']=bind(rb); ab=encode(am)
        sel['registry_binding']=bind(rb);sel['access_map_binding']=bind(ab)
        for n,b in [('registry',rb),('access-map',ab),('selection',encode(sel))]: (self.p/(n+'.json')).write_bytes(b)
        self.expected['budget']=budget
        save(self.p/'expected.json',self.expected)

def main():
    a=argparse.ArgumentParser();a.add_argument('--inputs',type=pathlib.Path,required=True);a.add_argument('--out',type=pathlib.Path,required=True);args=a.parse_args()
    root=args.out.resolve();root.mkdir(exist_ok=False)
    inp=args.inputs;result=(inp/'long-e-result.json').read_bytes();original=json.loads(result);npy=(inp/'frame0002_ifft_real.npy').read_bytes();npz=(inp/'stages-and-audio.npz').read_bytes()
    # Independent NPY header/byte audit; no correlation unpacking.
    import ast
    offset=10+struct.unpack_from('<H',npy,8)[0];hdr=ast.literal_eval(npy[10:offset].decode('ascii').strip())
    assert offset==128 and len(npy)==49280 and hdr=={'descr':'<i8','fortran_order':False,'shape':(6,1024)}
    with zipfile.ZipFile(io.BytesIO(npz)) as z: assert z.read('frame0002_ifft_real.npy')==npy
    def original_case(name,array=False):
        c=Case(root,name);c.source('r','result',result);c.expected_sources['r']=bind(result)
        if array:
            c.source('z','zip',npz);c.source('n','npy',npy,member_parent='z')
            c.expected_sources.update(z=bind(npz),n=bind(npy));c.expected['layouts']={'view0':[128,8320],'view1':[8320,16512]}
        c.view('r',original,2,0,array);c.view('r',original,2,1,array);return c
    c=original_case('saved_file');c.expected['read_ids']=['r'];c.freeze()
    c=original_case('saved_zip',True);c.expected['read_ids']=['r','z','n'];c.freeze()
    c=original_case('six_roles',True)
    for sid,role,name in [('i','index','saved-run-index.json'),('c','config','research-config.json'),('l','rule','fixed_golden.py')]:
        b=(inp/name).read_bytes();c.source(sid,role,b);c.expected_sources[sid]=bind(b)
    for v in c.views: v['support_ids']=['i','c','l']
    c.expected['read_ids']=['r','z','n','i','c','l'];c.freeze()
    # Small synthetic source tests: no altered old fixture/golden or historical claims.
    def synth(name,data=None):
        d=basic() if data is None else data;c=Case(root,name);b=encode(d);c.source('r','result',b);c.expected_sources['r']=bind(b);c.view('r',d);return c
    for field,value in [('decoder_role','WHITELIST_RULE_BYTES'),('scope_rule','WHITELIST_GLOBAL_RULE')]:
        c=synth('reject_'+field);c.expected_sources.clear();c.expected.update(processed=[False],facts={},identities={},units={},errors=[],result='UNSUPPORTED',read_ids=[])
        c.expected['unsupported_rules']=['UNSUPPORTED_ROLE_OR_SCOPE'];c.freeze(lambda r,m,s:r['entries'][0].update({field:value}))
    for field,value in [('schema_version','2'),('schema_sha256','a'*64),('encoding','SS_CANONICAL_JSON_V1')]:
        c=synth('reject_'+field);c.expected_sources.clear();c.expected.update(processed=[False],facts={},identities={},units={},errors=[],result='UNSUPPORTED',read_ids=[])
        c.expected['unsupported_rules']=['UNSUPPORTED_ROLE_OR_SCOPE']
        c.freeze(lambda r,m,s,f=field,v=value:(m['entries'][0]['ref'].update({f:v}),r['entries'][0]['source_schema'].update({f:v})))
    c=synth('reject_whitelist');c.expected_sources.clear();c.expected.update(processed=[False],facts={},identities={},units={},errors=[],result='UNSUPPORTED',read_ids=[],unsupported_rules=['SOURCE_NOT_WHITELISTED'])
    c.freeze(lambda r,m,s:r['entries'][0]['whitelist'][0].update(sha256='b'*64))
    for name,mut in [
        ('control_unknown',lambda r,m,s:s.update(extra='x')),
        ('control_number',lambda r,m,s:s['views'][0].update(pair_ordinal=0)),
        ('control_empty',lambda r,m,s:s.update(views=[])),
        ('control_reference',lambda r,m,s:s['views'][0].update(result_id='absent')),
        ('control_path',lambda r,m,s:m['entries'][0]['location'].update(path='../outside'))]:
        c=synth(name);c.expected.update(exit=2,failure_only=True);c.freeze(mut)
    c=synth('control_duplicate');c.expected.update(exit=2,failure_only=True);c.freeze();p=c.p/'selection.json';p.write_bytes(p.read_bytes().replace(b'"views": [',b'"schema_id":"ss-b-producer-selection-v1", "views": [',1))
    c=synth('control_binding');c.expected.update(exit=3,failure_only=True,failure_reason='CONTROL_BYTE_BINDING');c.freeze();p=c.p/'registry.json';p.write_bytes(p.read_bytes()+b' ')
    c=synth('existing_out');c.expected.update(exit=2,existing=True);c.freeze()
    for length,count,unicode in [(64,8,False),(65,9,False),(1024,1,False),(1025,1,False),(65,1,True)]:
        d=basic();reason=('界'*21+'ab') if unicode else 'X'*length
        d['stage_details'][0]['detail']['invalid_reasons']=[reason for _ in range(count)]
        d['stage_details'][0]['detail']['numeric_invalid']=True
        c=synth('errors_'+str(length)+'_'+str(count)+('_utf8' if unicode else ''),d)
        c.expected.update(exit=3,result='FAILED',conflict_rules=['ORIGINAL_NUMERIC_ERROR_REMAINS_INVALID']);c.freeze()
    for name,length_delta in [('source_hash',0),('source_length',1)]:
        c=Case(root,name);b=encode(basic());decl=bind(b);decl['sha256']='c'*64 if not length_delta else decl['sha256'];decl['byte_length']=str(len(b)+length_delta)
        c.source('r','result',b,declared=decl);c.view('r');c.expected.update(exit=3,result='FAILED',conflict_rules=['SOURCE_BYTE_IDENTITY'],read_ids=['r']);c.freeze()
    c=Case(root,'failed_read_budget');d0=basic();d1=basic();d1['test_marker']='different second source';b0=encode(d0);b1=encode(d1)
    c.source('r0','result',b0,declared={**bind(b0),'sha256':'d'*64});c.source('r1','result',b1)
    c.view('r0');c.view('r1');c.expected.update(exit=3,result='FAILED',conflict_rules=['SOURCE_BYTE_IDENTITY'],read_ids=['r0'],
        budget_failure={'first_length':len(b0),'second_length':len(b1),'forbidden_source':'r1','spent':len(b0)})
    c.freeze(budget=max(len(b0),len(b1)))
    for name,member in [('npy_endian',npy.replace(b"'<i8'",b"'>i8'",1)),('npy_shape',npy.replace(b'(6, 1024)',b'(3, 1024)',1))]:
        c=original_case(name);c.source('z','zip',archive(member));c.source('n','npy',member,member_parent='z')
        for v in c.views:v['array_view']={'state':'KNOWN','value':{'container_id':'z','member_id':'n','member_name':'frame0002_ifft_real.npy','row_ordinal':v['pair_ordinal']}}
        c.expected.update(exit=3,result='FAILED',conflict_rules=['NPY_LAYOUT_UNSUPPORTED'],no_layout=True);c.freeze()
    for name in ['zip_crc','zip_duplicate','zip_size']:
        c=original_case(name);zb=bytearray(archive(npy,duplicate=name=='zip_duplicate',stored=True))
        if name=='zip_crc':
            start=30+struct.unpack_from('<H',zb,26)[0]+struct.unpack_from('<H',zb,28)[0];zb[start+200]^=1
        if name=='zip_size':
            central=zb.find(b'PK\x01\x02');struct.pack_into('<I',zb,central+24,len(npy)-8);struct.pack_into('<I',zb,22,len(npy)-8)
        c.source('z','zip',bytes(zb));c.source('n','npy',npy,member_parent='z')
        for v in c.views:v['array_view']={'state':'KNOWN','value':{'container_id':'z','member_id':'n','member_name':'frame0002_ifft_real.npy','row_ordinal':v['pair_ordinal']}}
        c.expected.update(exit=3,result='FAILED',conflict_rules=[{'zip_crc':'ZIP_CRC_CONFLICT','zip_duplicate':'DUPLICATE_ZIP_MEMBER','zip_size':'ZIP_TRUE_EXPANDED_SIZE_CONFLICT'}[name]],no_layout=True);c.freeze()
    for depth in [64,65]:
        d=basic();x=0
        for _ in range(depth-1):x=[x]
        d['extension']=x;c=synth('json_depth_'+str(depth),d)
        if depth==65:
            c.expected.update(processed=[False],facts={},identities={},units={},errors=[],result='UNSUPPORTED',unsupported_rules=['JSON_DEPTH_LIMIT'])
        c.freeze()
    c=Case(root,'injected_post_failure');b=encode(basic());c.source('r','result',b,declared={**bind(b),'sha256':'e'*64});c.view('r')
    c.expected.update(exit=4,failure_only=True,failure_reason='TEST_INJECTED_POST_FAILURE',early_conflict='SOURCE_BYTE_IDENTITY',internal_injection=True);c.freeze()
    files={p.relative_to(root).as_posix():bind(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}
    save(root/'fixture-manifest.json',{'claim':'INDEPENDENT_EXPECTATIONS_FROZEN_BEFORE_DUT','files':files,'cases':[p.name for p in root.iterdir() if p.is_dir()]})
    print(json.dumps({'cases':len([p for p in root.iterdir() if p.is_dir()]),'manifest':bind((root/'fixture-manifest.json').read_bytes())}))

if __name__=='__main__':main()
