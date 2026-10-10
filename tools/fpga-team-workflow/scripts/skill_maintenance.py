"""Candidate editing and recoverable, user-scoped installation. No network writes.

Transactions replace only the named skill directory. Backups are never deleted.
All mutations require --execute and --authorization-ref; flags record the scope
the caller already authorized, not a source of authorization themselves.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import difflib
import json
import os
import shutil
import sys
import uuid
sys.dont_write_bytecode=True
from ftw_common import (PACKAGE, Refusal, digest, emit, file_hash, guard_main, no_links,
                        read, relative, require_schema, result, run, safe_path, tree, write_json)

RECEIPT='.ftw-install.json'
KINDS={'outer_rule','project_config','model_policy','model_runtime_adapter','tool_bridge','upstream_dependency','product_task'}

def verify_package(source, run_tests=False):
    source=no_links(source)
    errors=[]
    for rel in ('SKILL.md','VERSION','README.md','COMPATIBILITY.md','scripts/team_workflow.py','scripts/skill_maintenance.py','package-manifest.json'):
        if not safe_path(source,rel).is_file(): errors.append('Missing '+rel)
    if errors: return result('BLOCKED',errors=errors)
    manifest=read(source/'package-manifest.json'); require_schema(manifest)
    actual=tree(source,exclude=('package-manifest.json',RECEIPT))
    if manifest.get('files')!=actual: errors.append('Package manifest/content mismatch')
    if manifest.get('version')!=(source/'VERSION').read_text(encoding='utf-8').strip(): errors.append('Version mismatch')
    if (source/RECEIPT).exists():
        try:
            receipt=read(source/RECEIPT); require_schema(receipt)
            if receipt.get('name')!='fpga-team-workflow' or receipt.get('version')!=manifest.get('version'):
                errors.append('Installed receipt identity/version mismatch')
            if receipt.get('installed_files')!=tree(source,exclude=(RECEIPT,)):
                errors.append('Installed receipt/content mismatch')
            if not receipt.get('transaction_id'): errors.append('Installed receipt transaction missing')
        except (Refusal, ValueError) as exc:
            errors.append('Invalid installed receipt: '+str(exc))
    text=(source/'SKILL.md').read_text(encoding='utf-8')
    import yaml
    if not text.startswith('---\n'): errors.append('Missing skill frontmatter')
    else:
        front=yaml.safe_load(text.split('---',2)[1])
        if front.get('name')!='fpga-team-workflow' or not front.get('description'): errors.append('Invalid skill metadata')
    tests=None
    if run_tests and not errors:
        r=run([sys.executable,'-B','-m','unittest','discover','-s',str(source/'tests'),'-p','test_*.py','-v'],
              cwd=source,allowed=(0,1),timeout=180)
        tests={'exit_code':r.returncode,'output':(r.stdout+r.stderr).decode('utf-8',errors='replace')}
        if r.returncode: errors.append('Regression tests failed')
    return result('BLOCKED' if errors else 'OK', errors=errors, version=manifest.get('version'),
                  content_sha256=digest(actual),tests=tests,
                  review='Behavioral/user acceptance is separate from package validation')

def propose(feedback):
    require_schema(feedback)
    if feedback.get('kind','outer_rule') not in KINDS: raise Refusal('Unknown maintenance kind')
    if not feedback.get('problem') or not feedback.get('requested_behavior'): raise Refusal('Problem and requested behavior required')
    identity={k:feedback.get(k) for k in ('kind','problem','requested_behavior','scope')}
    return result(change_id='CHG-'+digest(identity)[:12],proposal=feedback,
                  dedupe_key=digest(identity),effective_rules_modified=False,
                  next_action='Compare dedupe_key in existing maintenance Issue; plan smallest owning layer')

def candidate(base, request, destination, execute=False):
    base=no_links(base); destination=no_links(destination)
    require_schema(request)
    if (base/RECEIPT).exists(): raise Refusal('Candidate base must be source, not installed copy')
    if request.get('kind') not in KINDS: raise Refusal('Unknown maintenance kind')
    current=tree(base)
    if not request.get('base_tree_sha256') or digest(current)!=request['base_tree_sha256']:
        raise Refusal('STALE_INPUT: candidate base fingerprint differs')
    if destination.exists() or destination.is_relative_to(base) or base.is_relative_to(destination):
        raise Refusal('Candidate must use a new disjoint destination')
    allowed=request.get('scope',{}).get('include',[])
    if not allowed or not request.get('protected_invariants') or not request.get('acceptance'):
        raise Refusal('Exact include paths, invariants and acceptance required')
    diffs=[]
    changes=request.get('changes',[])
    if not changes: raise Refusal('No concrete candidate changes')
    for item in changes:
        rel=relative(item['path'])
        if rel not in allowed or rel.startswith(('.codex/','.agents/')) or rel in {RECEIPT,'package-manifest.json'}:
            raise Refusal('Change outside exact owned scope: '+rel)
        p=safe_path(base,rel)
        old=p.read_text(encoding='utf-8') if p.is_file() else ''
        if item.get('base_sha256')!=(file_hash(p) if p.is_file() else None): raise Refusal('Changed baseline file: '+rel)
        new=item.get('content')
        if not isinstance(new,str): raise Refusal('v1 candidate editing supports explicit text replacement; deletion needs separate review')
        diffs.extend(difflib.unified_diff(old.splitlines(),new.splitlines(),fromfile='a/'+rel,tofile='b/'+rel,lineterm=''))
    if execute:
        shutil.copytree(base,destination)
        for item in changes:
            p=safe_path(destination,item['path']); p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(item['content'],encoding='utf-8')
        seal(destination)
    return result(dry_run=not execute,diff='\n'.join(diffs),candidate=str(destination),
                  tests='NOT_RUN: use verify --run-tests and independent forward test',installed_modified=False)

def seal(source):
    source=no_links(source)
    files=tree(source,exclude=('package-manifest.json',RECEIPT))
    manifest={'schema_version':1,'name':'fpga-team-workflow','version':(source/'VERSION').read_text(encoding='utf-8').strip(),'files':files}
    write_json(source/'package-manifest.json',manifest,overwrite=(source/'package-manifest.json').exists())
    return result(version=manifest['version'],files=len(files),content_sha256=digest(files))

def install_plan(source, target):
    source=no_links(source); target=no_links(target)
    if target.name!='fpga-team-workflow': raise Refusal('Target leaf must be fpga-team-workflow')
    if target.is_relative_to(source) or source.is_relative_to(target): raise Refusal('Source and target must be disjoint')
    check=verify_package(source)
    if check['status']!='OK': raise Refusal('Candidate invalid: '+str(check['errors']))
    if (source/RECEIPT).exists(): raise Refusal('Use a source/release package, not another installation')
    before=tree(target)
    after=tree(source)
    conflicts=[]
    receipt=None
    if before is not None:
        if not (target/RECEIPT).is_file(): conflicts.append('Unmanaged destination exists; never overwrite custom same-name skill')
        else:
            receipt=read(target/RECEIPT); require_schema(receipt)
            installed=tree(target,exclude=(RECEIPT,))
            if receipt.get('name')!='fpga-team-workflow' or installed!=receipt.get('installed_files'):
                conflicts.append('User edits/unknown files found since last managed installation')
    old={k:v for k,v in (before or {}).items() if k!=RECEIPT}
    delta={
        'create':sorted(set(after)-set(old)),
        'replace':sorted(k for k in set(after)&set(old) if after[k]!=old[k]),
        'remove_owned':sorted(set(old)-set(after)),
    }
    return result('BLOCKED' if conflicts else 'OK',action='install',source=str(source),target=str(target),
                  source_fingerprint=digest(after),target_fingerprint=digest(before),source_files=after,
                  before_files=before,version=check['version'],delta=delta,conflicts=conflicts,
                  idempotent=before is not None and not conflicts and old==after,
                  client_effect='New task/client refresh required; file installation does not prove active-session reload',
                  dependencies_changed=False,changes_global_config=False)

def _journal_path(transaction):
    transaction=no_links(transaction)
    journal=read(transaction/'transaction.json'); require_schema(journal)
    target=no_links(journal['target'])
    if target.name!='fpga-team-workflow' or transaction.parent!=target.parent/'.fpga-team-workflow-transactions':
        raise Refusal('Transaction ownership/path mismatch')
    if transaction.name!=journal.get('transaction_id'): raise Refusal('Transaction ID mismatch')
    return transaction,journal,target

def _save(transaction,journal):
    write_json(transaction/'transaction.json',journal,overwrite=(transaction/'transaction.json').exists())

def install(plan, execute=False, authorization_ref=None, failure_point=None):
    require_schema(plan)
    fresh=install_plan(plan['source'],plan['target'])
    if fresh['status']!='OK': raise Refusal('; '.join(fresh['conflicts']))
    for key in ('source_fingerprint','target_fingerprint','delta','version'):
        if fresh[key]!=plan.get(key): raise Refusal('STALE_PLAN: '+key)
    if not execute: return result(dry_run=True,plan=fresh)
    if not authorization_ref: raise Refusal('Installation authorization reference required')
    if fresh['idempotent']: return result(idempotent=True,transaction=None,files_changed=0,client_loaded='UNKNOWN')
    source,target=Path(fresh['source']),Path(fresh['target'])
    target.parent.mkdir(parents=True,exist_ok=True)
    lock=target.parent/'.fpga-team-workflow.install-lock'
    no_links(lock)
    fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
    txroot=no_links(target.parent/'.fpga-team-workflow-transactions')
    tx=txroot/uuid.uuid4().hex
    journal={'schema_version':1,'transaction_id':tx.name,'target':str(target),'source':str(source),
             'state':'PREPARING','before_files':fresh['before_files'],'after_files':None,
             'authorization_ref':authorization_ref,'version':fresh['version']}
    try:
        os.write(fd,json.dumps({'pid':os.getpid(),'transaction_id':tx.name}).encode())
        tx.mkdir(parents=True,exist_ok=False)
        _save(tx,journal)
        shutil.copytree(source,tx/'staging')
        if tree(tx/'staging')!=fresh['source_files']: raise Refusal('Staged copy mismatch')
        receipt={'schema_version':1,'name':'fpga-team-workflow','version':fresh['version'],
                 'transaction_id':tx.name,'installed_files':fresh['source_files']}
        write_json(tx/'staging'/RECEIPT,receipt)
        journal['after_files']=tree(tx/'staging')
        journal['state']='READY'; _save(tx,journal)
        # Recheck immediately before mutation, in addition to exclusive tool-local lock.
        if digest(tree(target))!=fresh['target_fingerprint']: raise Refusal('STALE_PLAN at switch')
        if target.exists(): target.rename(tx/'backup')
        journal['state']='BACKED_UP'; _save(tx,journal)
        if failure_point=='after_backup': raise OSError('Injected installation failure after backup')
        (tx/'staging').rename(target)
        journal['state']='SWITCHED'; _save(tx,journal)
        if failure_point=='after_switch': raise OSError('Injected installation failure after switch')
        if tree(target)!=journal['after_files']: raise Refusal('Post-install content mismatch')
        journal['state']='INSTALLED'; _save(tx,journal)
        return result(transaction=str(tx),version=fresh['version'],files_verified=len(fresh['source_files']),
                      files_changed=len(fresh['delta']['create'])+len(fresh['delta']['replace'])+len(fresh['delta']['remove_owned']),
                      client_loaded='UNKNOWN',recovery_command=f'python scripts/skill_maintenance.py recover --transaction "{tx}" --execute --authorization-ref <request-ref>')
    except Exception as exc:
        if tx.exists():
            try:
                recover(tx,execute=True,authorization_ref=authorization_ref)
            except Exception as recovery_error:
                raise Refusal(f'Installation failed: {exc}; recovery blocked: {recovery_error}; preserve {tx}') from exc
        raise Refusal(f'Installation failed and previous state restored: {exc}; transaction={tx}') from exc
    finally:
        os.close(fd)
        lock.unlink()

def recover(transaction, execute=False, authorization_ref=None):
    if execute and not authorization_ref: raise Refusal('Recovery authorization required')
    tx,journal,target=_journal_path(transaction)
    if journal['state'] in {'INSTALLED','ROLLED_BACK'}: raise Refusal('Completed transaction: use rollback, not recovery')
    before,after=journal['before_files'],journal['after_files']
    current=tree(target)
    if current==before:
        if execute:
            journal['state']='RECOVERED'; _save(tx,journal)
        return result(recovered=True,dry_run=not execute,target=str(target))
    if current is not None and current!=after: raise Refusal('Unknown destination changes; recovery refuses overwrite')
    if before is not None and tree(tx/'backup')!=before: raise Refusal('Backup missing or modified')
    if execute:
        if not authorization_ref: raise Refusal('Recovery authorization required')
        if target.exists(): target.rename(tx/'failed-install')
        if before is not None: (tx/'backup').rename(target)
        if tree(target)!=before: raise Refusal('Recovery verification failed')
        journal['state']='RECOVERED'; _save(tx,journal)
    return result(recovered=execute,dry_run=not execute,target=str(target))

def rollback(transaction, execute=False, authorization_ref=None):
    tx,journal,target=_journal_path(transaction)
    if journal['state']=='ROLLED_BACK':
        if tree(target)!=journal['before_files']: raise Refusal('Post-rollback user changes; stop')
        return result(idempotent=True,dry_run=not execute)
    if journal['state']!='INSTALLED': raise Refusal('Transaction not installed; use recover')
    if tree(target)!=journal['after_files']: raise Refusal('Post-install user modifications; rollback refuses overwrite')
    before=journal['before_files']
    if before is not None and tree(tx/'backup')!=before: raise Refusal('Backup changed or missing')
    if not execute: return result(dry_run=True,target=str(target),restore_version='previous managed directory or absence')
    if not authorization_ref: raise Refusal('Rollback authorization reference required')
    retired=tx/'rolled-back-install'
    if retired.exists(): raise Refusal('Retired install already exists; inspect interrupted rollback')
    target.rename(retired)
    try:
        if before is not None: (tx/'backup').rename(target)
        if tree(target)!=before: raise Refusal('Rollback verification failed')
    except Exception:
        if not target.exists(): retired.rename(target)
        raise
    journal['state']='ROLLED_BACK'; _save(tx,journal)
    return result(rolled_back=True,target=str(target),verified=True,product_files_changed=False)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action',choices=['propose','plan','apply','verify','seal','publish','install-plan','install','rollback','recover'])
    ap.add_argument('--source');ap.add_argument('--target');ap.add_argument('--request');ap.add_argument('--plan')
    ap.add_argument('--transaction');ap.add_argument('--out');ap.add_argument('--execute',action='store_true')
    ap.add_argument('--dry-run',action='store_true');ap.add_argument('--authorization-ref');ap.add_argument('--run-tests',action='store_true')
    args=ap.parse_args()
    execute=args.execute and not args.dry_run
    if args.execute and args.dry_run: raise Refusal('Choose --execute or --dry-run')
    if execute and not args.authorization_ref: raise Refusal('Mutation requires an existing authorization reference')
    if args.action=='propose': out=propose(read(args.request))
    elif args.action=='plan':
        p=propose(read(args.request)); out=result(proposal=p,minimal_layer=p['proposal'].get('kind'),
            baseline=tree(args.source) if args.source else None,plan='Edit exact include paths in a new candidate; verify tests; preserve installed and upstream files; install from fingerprinted preview; rollback by transaction')
    elif args.action=='apply': out=candidate(args.source,read(args.request),args.target,execute)
    elif args.action=='verify': out=verify_package(args.source,args.run_tests)
    elif args.action=='seal':
        if not execute: out=result(dry_run=True,source=args.source,files=tree(args.source))
        else: out=seal(args.source)
    elif args.action=='install-plan': out=install_plan(args.source,args.target)
    elif args.action=='install': out=install(read(args.plan),execute,args.authorization_ref)
    elif args.action=='rollback': out=rollback(args.transaction,execute,args.authorization_ref)
    elif args.action=='recover': out=recover(args.transaction,execute,args.authorization_ref)
    else:
        out=result('NEEDS_USER_ACTION',action='publish',verification=verify_package(args.source),
                   remote_published=False,requirements=['Qualified non-author member or designated-AI approval under project policy','Repository/tag and publication authorization'],
                   artifacts=['VERSION','package-manifest.json','CHANGELOG.md','COMPATIBILITY.md'],
                   next_action='Use authorized GitHub tool/human to publish exact candidate; record returned URL/commit, never synthesize success')
    return emit(out,args.out)

if __name__=='__main__': guard_main(main)
