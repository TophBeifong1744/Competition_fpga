"""Finite independent output oracle. No import from any product module."""
import argparse, hashlib, json, pathlib, sys

class Rejected(Exception):pass
def demand(ok,category,detail=''):
    if not ok:raise Rejected(category+': '+detail)
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def binding(p):
    b=p.read_bytes();return {'sha256':hashlib.sha256(b).hexdigest(),'byte_length':str(len(b))}
def rules(items):return [i['rule'] for i in items]
def check(case,run):
    e=load(case/'expected.json');inv=load(run/'invocation.json');out=run/'dut'
    demand(inv['exit']==e['exit'],'EXIT',str((e['exit'],inv['exit'])))
    if e.get('existing'):
        demand(binding(out/'sentinel.bin')==inv['sentinel_before'],'OUTPUT_PROTECTION')
        demand(sorted(p.name for p in out.iterdir())==['sentinel.bin'],'OUTPUT_PROTECTION')
        demand('OUTPUT_EXISTS' in (run/'stderr.txt').read_text(encoding='utf-8'),'OUTPUT_PROTECTION')
        return
    if e.get('failure_only'):
        demand(not (out/'report.json').exists() and not (out/'output-index.json').exists(),'FAILURE_ONLY')
        f=load(out/'failure.json');demand(f['output_state']=='FAILURE_ONLY' and f['V']=='NOT_RUN','FAILURE_ONLY')
        if e.get('failure_reason'):demand(f['run']['first_error']['reason']==e['failure_reason'],'FAILURE_REASON')
        if e.get('early_conflict'):demand(e['early_conflict'] in rules(f['known_conflicts']),'EARLY_ERROR')
        return
    r=load(out/'report.json')
    # Budget assertion first: canary reaches the resource rule, not a later count/hash failure.
    if e.get('budget_failure'):
        b=e['budget_failure'];records=r['source_audit']['actual_read_set']
        demand(b['forbidden_source'] not in [s['id'] for s in records],'RESOURCE_BUDGET','second source was actually read after exhausted budget')
        demand(any(b['forbidden_source'] in s['source_ids'] and ('BUDGET' in s['rule'] or 'RESOURCE' in s['rule']) for s in r['unsupported']),
               'RESOURCE_BUDGET','missing explicit affected-source resource refusal')
        demand(int(r['source_audit']['distinct_source_bytes'])==b['spent'],'RESOURCE_BUDGET','actual failed acquisition not charged')
    demand(r['output_state']=='SEALED_REPORT' and r['producer_result']==e['result'],'RESULT')
    demand(r['claim_scope']=='SAVED_RESEARCH_DIAGNOSTIC' and r['v_status']=='NOT_RUN' and r['wire_ready']=='0' and r['time']=='UNBOUND','NO_ESCALATION')
    # Every finite case lacks independently supplied complete K/roots/context.
    demand(bool(r['missing']),'MISSING_EVIDENCE','source-context/native gaps disappeared')
    views=r['views'];c=r['counts'];sel=load(case/'selection.json')
    demand(int(c['requested_views'])==len(sel['views'])==len(views),'DENOMINATOR')
    demand(int(c['processed_views'])+int(c['not_processed_views'])==len(views),'DENOMINATOR')
    demand([v['id'] for v in views]==[v['id'] for v in sel['views']],'IDENTITY','selected view IDs/order changed')
    demand([v['selection'] for v in views]==sel['views'],'IDENTITY','selector substitution')
    demand([v['processed'] for v in views]==e['processed'],'PROCESSED')
    demand(int(c['processed_views'])==sum(e['processed']),'DENOMINATOR')
    for v in views:
        vid=v['id']
        if vid in e['facts']:
            fs=v['facts'];demand(len(fs)==len({f['name'] for f in fs}),'FACTS','duplicate saved fact')
            actual={f['name']:f['value']['value'] for f in fs};demand(actual==e['facts'][vid],'FACTS',vid)
            for f in fs:
                expectedloc='/stage_details/'+v['selection']['stage_ordinal']+'/detail/pair_rows/'+v['selection']['pair_ordinal']+'/'+f['name']
                demand(f['source_id']==v['selection']['result_id'] and f['locator']==expectedloc and f['degree']=='KNOWN_SAVED','FACT_SOURCE')
            demand({k:x['value'] for k,x in v['partial_identity'].items() if x['state']=='KNOWN'}==e['identities'][vid],'IDENTITY')
            demand(v['saved_status']==e['units'][vid],'ORIGINAL_STATUS')
        if vid in e.get('layouts',{}):
            a=v.get('array_view',{});demand([int(x) for x in a.get('row_byte_span',[])]==e['layouts'][vid],'LAYOUT')
            demand(a['layout']=={'version':'1.0','dtype':'<i8','fortran_order':False,'shape':['6','1024'],'data_offset':'128','code_decode':'NOT_RUN'},'LAYOUT')
        if e.get('no_layout'):demand('array_view' not in v,'LAYOUT','invalid source acquired a layout')
    er=r['original_errors'];demand(len(er)==len(e['errors']),'ERRORS','error lost/duplicated')
    for name in ('conflicts','missing','unsupported','original_errors'):
        demand(int(c[name])==len(r[name]),'AXIS_COUNTS',name)
    for x,y in zip(er,e['errors']):
        demand(x['source_id']==y['source_id'] and x['locator']==y['locator'] and int(x['reason_utf8_bytes'])==y['utf8'],'ERRORS')
        rr=x['raw_reason']
        demand(rr=={'state':'KNOWN','value':y['text']} if y['utf8']<=1024 else rr['state']=='UNKNOWN','ERRORS','wrong reason representation')
        demand(x['typed_error_ref']['state']=='UNKNOWN','NO_ESCALATION')
        demand(('WOULD_EXCEED_ERROR_REASON_64_UTF8_BYTES' in x['representation_issues'])==(y['utf8']>64),'ERRORS')
        demand(('RAW_TEXT_1024_BYTES_EXCEEDED_USE_ORIGINAL_SOURCE' in x['representation_issues'])==(y['utf8']>1024),'ERRORS')
    demand(bool(r['error_capacity_issues'])==(len(er)>8),'ERRORS','slot capacity')
    for axis in ('conflict','unsupported'):
        for rule in e.get(axis+'_rules',[]):demand(rule in rules(r['conflicts' if axis=='conflict' else 'unsupported']),'SOURCE' if axis=='conflict' else 'DISPATCH',rule)
    audit=r['source_audit'];records=audit['actual_read_set'];ids=[x['id'] for x in records]
    if 'read_ids' in e:demand(ids==e['read_ids'],'SOURCE','read set/order')
    demand(int(c['actual_read_sources'])==len(records) and int(c['permission_sources'])==len(load(case/'access-map.json')['entries']),'SOURCE')
    demand(int(audit['distinct_source_bytes'])<=e['budget'],'RESOURCE_ACCOUNTING')
    for sid,h in e['sources'].items():
        match=[x for x in records if x['id']==sid];demand(len(match)==1 and match[0]['observed']==h and match[0]['post']=='UNCHANGED','SOURCE',sid)
        p=out/'originals'/(h['sha256']+'.bin');demand(p.is_file() and binding(p)==h,'ORIGINALS',sid)
    if e['sources'] and set(e['sources'])==set(ids):
        distinct={h['sha256']:int(h['byte_length']) for h in e['sources'].values()}
        demand(int(audit['distinct_source_bytes'])==sum(distinct.values()),'RESOURCE_ACCOUNTING','source/member byte total')
    demand(set(audit['consumed_closure'])<=set(ids),'SOURCE','consumed unread source')
    for n,filename in [('registry','registry.json'),('access_map','access-map.json'),('selection','selection.json')]:
        demand(r['input_bindings'][n]==binding(case/filename),'CONTROL_BINDING')
    for raw in r['raw_payloads']:
        p=out/raw['path'];b=load(p)
        demand(b['audit']['result']=='NOT_RUN' and b['events']==[] and b['key_wire']['state']=='UNKNOWN' and b['roots_wire']['state']=='UNKNOWN','RAW_STATUS')
        demand(all(x['state']!='CHECKED_SOURCE' for x in b['coverage']),'RAW_STATUS')
        for obj in b['objects']:demand(obj['key_wire']['state']=='UNKNOWN' and obj['lifetime']['state']=='UNKNOWN','RAW_STATUS')
        demand(binding(p)=={k:raw[k] for k in ('sha256','byte_length')},'OUTPUT_IDENTITY')
    index=load(out/'output-index.json');demand(index['exit']==str(e['exit']),'OUTPUT_IDENTITY')
    for rel,h in index['files'].items():
        p=(out/rel).resolve();demand(p.is_relative_to(out.resolve()),'OUTPUT_PATH')
        demand(p.is_file() and binding(p)==h,'OUTPUT_IDENTITY',rel)

def main():
    a=argparse.ArgumentParser();a.add_argument('--case',type=pathlib.Path,required=True);a.add_argument('--run',type=pathlib.Path,required=True);args=a.parse_args()
    try:check(args.case,args.run)
    except (Rejected,KeyError,ValueError,OSError,TypeError) as e:
        print('CHECK_REJECTED '+str(e),file=sys.stderr);return 1
    print('CHECK_OK '+args.case.name);return 0
if __name__=='__main__':sys.exit(main())
