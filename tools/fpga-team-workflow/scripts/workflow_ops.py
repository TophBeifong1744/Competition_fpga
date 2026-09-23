"""Repository, workspace, evidence and handoff operations with explicit boundaries."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import csv
import io
import json
import os
import re
import shutil
import sys
import uuid
from ftw_common import (PACKAGE, Refusal, contains, digest, file_hash, git, git_state,
                        no_links, read, relative, require_schema, result, run, safe_path, tree, write_json)
from model_policy import recommend, validate_policy

def upstream_check(skill, agents):
    lock = read(PACKAGE/'assets/upstream-lock.json')
    missing, changed = [], []
    for key, expected in lock['files'].items():
        area, rel = key.split('/', 1)
        p = safe_path(skill if area == 'skill' else agents, rel)
        if not p.is_file(): missing.append(key)
        elif file_hash(p) != expected: changed.append(key)
    return result('BLOCKED' if missing or changed else 'OK',
                  dependency_version=lock['version'], source_commit=lock['source_commit'],
                  files_checked=len(lock['files']), roles_expected=13, missing=missing, changed=changed,
                  client_loaded='UNKNOWN', technical_acceptance='NOT_RUN')

def _layout(config, target=None):
    require_schema(config)
    if config.get('targets'):
        if not target:
            raise Refusal('Multiple targets require explicit --target')
        targets = config['targets']
        matches = [x for x in targets if x.get('id') == target]
        if len(matches) != 1:
            raise Refusal('Target missing or ambiguous')
        return matches[0]['layout']
    return config.get('layout', {})

def declared_paths(layout):
    keys = ['upstream_project_root', 'document_root', 'project_entry']
    result_paths = [layout[k] for k in keys if layout.get(k) is not None]
    for key, value in layout.items():
        if key.endswith('_roots') and isinstance(value, list): result_paths.extend(value)
    for key in ('filelist_refs', 'entry_refs', 'runtime_roots'):
        result_paths.extend(x for x in layout.get(key, {}).values() if x is not None)
    for key in ('source_exceptions', 'required_inputs'):
        result_paths.extend(layout.get(key, []))
    return result_paths

def dependency_view(root, layout):
    """Conservative plain filelist adapter, not a Vivado source-view interpreter."""
    sources, include_dirs, lists, unsupported = set(), set(), set(), []
    errors = []
    def add_filelist(value):
        value = relative(value)
        if value in lists: return
        lists.add(value)
        p = safe_path(root, value)
        if not p.is_file():
            errors.append('Missing filelist: ' + value)
            return
        for raw in p.read_text(encoding='utf-8-sig').splitlines():
            line = raw.strip()
            if not line or line.startswith(('#', '//')): continue
            if line.startswith('+incdir+'):
                for rel in line[len('+incdir+'):].split('+'):
                    safe_path(root, rel)
                    include_dirs.add(relative(rel))
            elif line.startswith('+define+'):
                continue
            elif line.startswith('-f '):
                add_filelist(line[3:].strip().strip('"'))
            elif line.startswith(('-', '+')) or '$' in line:
                unsupported.append(line)
            else:
                sources.add(relative(line.strip('"')))
    for rel in layout.get('filelist_refs', {}).values():
        if rel is not None: add_filelist(rel)
    for rel in layout.get('required_inputs', []): sources.add(relative(rel))
    if layout.get('project_entry') and layout.get('project_control') == 'native_project':
        sources.add(relative(layout['project_entry']))
    for rel in layout.get('source_exceptions', []):
        p = safe_path(root, rel)
        if p.is_file(): sources.add(relative(rel))
        elif p.is_dir():
            for f in tree(p): sources.add((Path(rel)/f).as_posix())
        else: errors.append('Missing protected source: ' + rel)
    queue = list(sources)
    modules = {}
    while queue:
        rel = queue.pop()
        p = safe_path(root, rel)
        if not p.is_file():
            errors.append('Missing input: ' + rel)
            continue
        if p.suffix.lower() not in {'.v', '.sv', '.vh', '.svh'}: continue
        text = p.read_text(encoding='utf-8-sig')
        stripped = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
        for module in re.findall(r'\bmodule\s+(?:automatic\s+)?([A-Za-z_][\w$]*)', stripped):
            modules.setdefault(module, set()).add(rel)
        for header in re.findall(r'`include\s+"([^"]+)"', stripped):
            header = relative(header)
            options = [Path(rel).parent/header, *(Path(x)/header for x in sorted(include_dirs))]
            candidates = [x.as_posix() for x in options if safe_path(root, x.as_posix()).is_file()]
            if not candidates:
                errors.append('Missing include: ' + rel + ' -> ' + header)
            else:
                selected = candidates[0]
                if selected not in sources:
                    sources.add(selected)
                    queue.append(selected)
        for data in re.findall(r'\$readmem[hb]\s*\(\s*"([^"]+)"', stripped):
            if relative(data) not in sources:
                errors.append('Initialization data must be declared in required_inputs: ' + data)
    duplicates = {m: sorted(v) for m, v in modules.items() if len(v) > 1}
    for m, paths in duplicates.items(): errors.append('Duplicate loaded module ' + m + ': ' + ', '.join(paths))
    return {'files': sorted(sources), 'include_dirs': sorted(include_dirs), 'filelists': sorted(lists),
            'errors': sorted(set(errors)), 'unsupported': sorted(set(unsupported)), 'duplicate_modules': duplicates,
            'scope': 'Explicit plain filelists and literal includes only; vendor source view, conditional preprocessing and external dependencies require adapter evidence'}

def inspect_layout(root, config, target=None):
    root = no_links(root)
    layout = _layout(config, target)
    require_schema(layout)
    if layout.get('mode') not in {'canonical', 'existing'} or layout.get('project_control') not in {'script', 'native_project'}:
        raise Refusal('Unsupported layout mode or project_control')
    for rel in declared_paths(layout): safe_path(root, rel)
    for rel in config.get('workspace', {}).get('protected_paths', []): safe_path(root, rel)
    view = dependency_view(root, layout)
    errors, warnings = list(view['errors']), []
    if view['unsupported']: warnings.append('Filelist adapter does not support all syntax')
    if layout.get('adapter_status') != 'VERIFIED' or not layout.get('adapter_evidence_ref'):
        warnings.append('Real build adapter is UNVERIFIED; mapping is not execution compatibility')
    entry = layout.get('project_entry')
    if entry:
        if not safe_path(root, entry).is_file(): errors.append('Missing project entry: ' + entry)
        if layout['mode'] == 'canonical':
            expected = (Path(layout.get('upstream_project_root', '.'))/'project/par').as_posix()
            if Path(entry).parent.as_posix() != expected: errors.append('Canonical project entry must be directly under project/par')
    else:
        warnings.append('No real vendor project entry configured')
    protected = layout.get('source_exceptions', []) + config.get('workspace', {}).get('protected_paths', [])
    for rel in view['files']:
        for name, output in layout.get('runtime_roots', {}).items():
            if output and contains(output, rel) and not any(contains(p, rel) for p in protected):
                errors.append('Source in runtime area without protection: ' + rel)
    ignored, untracked, output_tracked = [], [], []
    if (root/'.git').exists():
        tracked = set(git(root, 'ls-files', '-z').split('\0'))
        for rel in view['files'] + view['filelists']:
            r = run(['git', '-C', root, 'check-ignore', '--no-index', '-q', '--', rel], allowed=(0, 1))
            if r.returncode == 0: ignored.append(rel)
            if rel not in tracked: untracked.append(rel)
        for rel in tracked - {''}:
            if any(contains(p, rel) for p in layout.get('regenerable_output_roots', [])) and not any(contains(p, rel) for p in protected):
                output_tracked.append(rel)
        if ignored: errors.append('Required sources are ignored')
        if untracked: warnings.append('Required files are untracked; formal handoff blocked')
        if output_tracked: errors.append('Declared regenerable outputs are tracked')
    else: warnings.append('Not a repository; Git ownership checks not run')
    if config.get('targets'):
        runtime = []
        for item in config['targets']:
            for value in item['layout'].get('runtime_roots', {}).values():
                if value:
                    for prev_id, prev in runtime:
                        if item['id'] != prev_id and (contains(prev, value) or contains(value, prev)):
                            errors.append('Mutable output overlap across targets: ' + value)
                    runtime.append((item['id'], value))
    return result('BLOCKED' if errors else 'INCONCLUSIVE' if warnings else 'OK', layout_mode=layout['mode'],
                  target=target, dependencies=view, errors=errors, warnings=warnings,
                  ignored_sources=ignored, untracked_required=untracked, tracked_outputs=output_tracked,
                  product_modified=False, engineering_entry_verified=False)

def init_layout(root, config, execute=False):
    require_schema(config)
    root = no_links(root)
    layout = _layout(config)
    require_schema(layout)
    if layout.get('mode') != 'canonical':
        raise Refusal('Existing layouts are inspection-only; no implicit migration')
    if root.exists() and any(root.iterdir()):
        raise Refusal('Initialization requires an empty destination; existing projects use mapping')
    pid = config.get('project', {}).get('id')
    if not pid or pid.startswith('REPLACE_'): raise Refusal('Project ID required')
    dirs = ['document', 'project/rtl', 'project/sdc', 'project/script', 'project/par',
            'simulation/tb', 'simulation/script', 'linter/script', 'release/manifests']
    for key in ('ip_roots', 'bd_roots', 'model_roots', 'software_roots', 'fixture_roots'):
        dirs.extend(layout.get(key, []))
    for rel in dirs: safe_path(root, rel)
    if execute:
        for rel in dirs: safe_path(root, rel).mkdir(parents=True, exist_ok=True)
        write_json(root/'team-workflow.yaml', config)
        (root/'.gitignore').write_text((PACKAGE/'assets/repository-gitignore.example').read_text(encoding='utf-8'),encoding='utf-8')
        (root/'document/project-identity.md').write_text('# '+pid+'\n\nVendor tool, part and real entry: UNVERIFIED. No engineering acceptance.\n',encoding='utf-8')
    return result(dry_run=not execute, directories=dirs, project_files_created=False,
                  engineering_status='UNVERIFIED', reason='Documentation/layout initialization only; vendor-native tools create real project files')

def process_observation():
    """Conservative local process-name observation, not a cross-machine lock."""
    if os.name != 'nt':
        return {'known': False, 'reason': 'Process detector validated on Windows only', 'active': []}
    r = run(['tasklist.exe', '/FO', 'CSV', '/NH'])
    raw = r.stdout.decode('oem', errors='replace')
    names = {'vivado.exe', 'xsim.exe', 'xelab.exe', 'xvlog.exe', 'vsim.exe', 'vlog.exe', 'quartus.exe', 'vitis.exe'}
    active = [row[:2] for row in csv.reader(io.StringIO(raw)) if row and row[0].lower() in names]
    return {'known': True, 'active': active, 'scope': 'local process names; other sessions require explicit occupancy observation'}

def workspace_plan(root, task, config, occupancy=None, target=None):
    require_schema(task)
    state = git_state(root)
    view = inspect_layout(root, config, target)
    layout = _layout(config, target)
    occupancy = occupancy or {'schema_version': 1, 'writer_clear': False, 'source_ref': None}
    require_schema(occupancy)
    processes = process_observation()
    blockers = []
    if state['porcelain']: blockers.append('Dirty, untracked or ignored work exists; protect it before switch/sparse operations')
    if not occupancy.get('writer_clear') or not occupancy.get('source_ref'): blockers.append('Single-writer occupancy not confirmed')
    if occupancy.get('active') or processes['active']: blockers.append('Active EDA/build or writer occupies input directory')
    if not processes['known']: blockers.append('Local process observation unavailable')
    if view['errors'] or view['dependencies']['unsupported']: blockers.append('Dependency/source checks failed or unsupported')
    base = task.get('base_commit')
    if not base or not re.fullmatch(r'[0-9a-f]{40,64}', base): blockers.append('Resolved base commit required')
    elif git(root, 'rev-parse', base+'^{commit}').strip() != base: blockers.append('Base identity mismatch')
    strategy = 'isolate' if task.get('parallel_write') or task.get('independent_reproduction') else 'sparse' if task.get('sparse_requested') else 'reuse'
    deps = set(view['dependencies']['files'] + view['dependencies']['filelists'])
    for value in layout.get('entry_refs', {}).values():
        if value: deps.add(value)
    deps.update(task.get('dependency_files', []))
    tracked = [x for x in git(root, 'ls-files', '-z').split('\0') if x]
    # Keep inherited instructions and project-local installed skills/roles across sparse scope.
    deps.update(p for p in tracked if Path(p).name == 'AGENTS.md' or '/.agents/skills/' in '/'+p or '/.codex/agents/' in '/'+p)
    deps.update(p for p in ('team-workflow.yaml', 'workflow-lock.yaml') if (Path(root)/p).is_file())
    for p in deps:
        if not safe_path(root,p).is_file(): blockers.append('Missing selected dependency: '+p)
    dirs = sorted({str(Path(p).parent).replace('\\','/') for p in deps if str(Path(p).parent) != '.'})
    if strategy in {'sparse', 'isolate'} and (not task.get('dependency_closure_ref') or layout.get('adapter_status') != 'VERIFIED' or not layout.get('adapter_evidence_ref')):
        blockers.append('Sparse/isolation requires evidence of complete dependencies and a verified entry')
    branch = task.get('branch') or state['branch']
    if base and base != state['head'] and (branch != state['branch'] or strategy == 'isolate'):
        blockers.append('Selected base differs from inspected HEAD; inspect an exact-base checkout before planning branch/worktree creation')
    if not branch or run(['git','check-ref-format','--branch',branch], allowed=(0,128)).returncode:
        blockers.append('Invalid target branch')
    return result('BLOCKED' if blockers else 'OK', root=str(no_links(root)), strategy=strategy,
                  base_commit=base, branch=branch, state=state, task=task, config_hash=digest(config),
                  occupancy=occupancy, processes=processes, dependency_files=sorted(deps), sparse_dirs=dirs,
                  dependency_hashes={p:file_hash(safe_path(root,p)) for p in deps if safe_path(root,p).is_file()},
                  blockers=blockers, advisory_only=True, layout_report=view)

def workspace_apply(plan, config, occupancy, execute=False, isolation_destination=None):
    require_schema(plan)
    if plan.get('status') != 'OK': raise Refusal('Plan is not applicable')
    root = no_links(plan['root'])
    current = workspace_plan(root, plan['task'], config, occupancy, plan.get('layout_report',{}).get('target'))
    if current['status'] != 'OK': raise Refusal('; '.join(current['blockers']))
    for key in ('state','config_hash','dependency_files','dependency_hashes','strategy','sparse_dirs','branch'):
        if current[key] != plan[key]: raise Refusal('STALE_PLAN: '+key)
    branch, strategy = plan['branch'], plan['strategy']
    commands = []
    existing = git(root, 'rev-parse', '--verify', '--quiet', 'refs/heads/'+branch, allowed=(0,1)).strip()
    if existing and existing.split()[0] != plan['base_commit'] and branch != plan['state']['branch']:
        raise Refusal('Existing target branch moved away from planned base')
    if strategy == 'isolate':
        if not isolation_destination: raise Refusal('Explicit isolation destination required')
        dest = no_links(isolation_destination)
        if dest.exists() or dest.is_relative_to(root) or root.is_relative_to(dest):
            raise Refusal('Isolation destination must be new and outside current checkout')
        if existing: raise Refusal('Isolation uses a new branch; select a unique branch')
        commands.append(['git','-C',str(root),'worktree','add','--no-checkout','-b',branch,str(dest),plan['base_commit']])
        commands.append(['git','-C',str(dest),'sparse-checkout','set','--cone','--',*plan['sparse_dirs']])
        commands.append(['git','-C',str(dest),'checkout',branch])
    else:
        if branch != plan['state']['branch']:
            commands.append(['git','-C',str(root),'switch',branch] if existing else
                            ['git','-C',str(root),'switch','-c',branch,plan['base_commit']])
        if strategy == 'sparse': commands.append(['git','-C',str(root),'sparse-checkout','set','--cone','--',*plan['sparse_dirs']])
    if execute:
        lock_path = Path(git(root,'rev-parse','--git-path','ftw-workspace.lock').strip())
        if not lock_path.is_absolute(): lock_path=root/lock_path
        no_links(lock_path)
        fd=os.open(lock_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
        try:
            os.write(fd,str(os.getpid()).encode())
            for cmd in commands: run(cmd)
        finally:
            os.close(fd)
            lock_path.unlink()
    return result(dry_run=not execute, commands=commands, strategy=strategy,
                  lock_scope='local advisory; not a distributed lock',
                  failure_recovery='On command failure retain worktree/branch; inspect status and resume, never reset/clean automatically')

def snapshot(root, inputs, previous=None):
    require_schema(inputs)
    files = sorted(set(inputs.get('files', [])))
    if not files: raise Refusal('Explicit input file list required')
    root=no_links(root)
    hashes={p:file_hash(safe_path(root,p)) for p in files}
    end={p:file_hash(safe_path(root,p)) for p in files}
    identities={'files':hashes,'context':inputs.get('context',{})}
    state=git_state(root)
    tracked=set(git(root,'ls-files','-z').split('\0'))
    data=result(root=str(root),head=state['head'], input_identity=digest(identities),
                identities=identities, untracked_inputs=sorted(set(files)-tracked),
                stable_during_capture=hashes==end,
                dirty_diff_sha256=digest(git(root,'diff','HEAD','--',*files)),
                run_stability='UNKNOWN: compare independent start/end snapshots around the actual run')
    if previous:
        require_schema(previous)
        data['matches_previous_inputs']=previous.get('input_identity')==data['input_identity']
        if not data['matches_previous_inputs']: data['status']='BLOCKED'
    if hashes!=end: data['status']='BLOCKED'
    return data

def evidence_inspect(index, current, evidence_root=None):
    require_schema(index); require_schema(current)
    reasons, unknown = [], []
    if index.get('assumption_conflicts') or current.get('assumption_conflicts'):
        reasons.append('Acceptance assumptions/reference contradicted; prior PASS invalid')
    if index.get('checker_invalid') or current.get('checker_invalid'):
        reasons.append('Checker invalid; prior PASS invalid')
    keys = ('requirements','sources','constraints','parameters','dependencies','checker','reference','input_data','tool','entry')
    a,b=index.get('identities',{}),current.get('identities',{})
    for k in keys:
        if k not in a or k not in b or a[k] is None or b[k] is None: unknown.append('Missing identity: '+k)
        elif a[k] != b[k]: reasons.append('Changed relevant identity: '+k)
    if index.get('run_inputs_stable') is not True: unknown.append('Run start/end stability unproven')
    records=index.get('raw_records',[])
    if not records: unknown.append('Raw evidence missing')
    native=[]
    for record in records:
        if record.get('schema_version') not in (1,'1.0','1.0.0'):
            unknown.append('Unsupported native schema: '+str(record.get('schema_version')))
        if not evidence_root or not record.get('local_path'):
            unknown.append('Raw evidence accessibility/hash not independently checked')
            continue
        p=safe_path(evidence_root,record['local_path'])
        if not p.is_file(): unknown.append('Raw evidence unavailable: '+record['local_path'])
        elif not record.get('sha256') or file_hash(p)!=record['sha256']: reasons.append('Raw evidence hash mismatch')
        elif p.suffix.lower()=='.json':
            raw=read(p)
            if not isinstance(raw,dict) or raw.get('schema_version')!=record.get('schema_version'):
                unknown.append('Raw schema differs from descriptor: '+record['local_path'])
                continue
            kind=record.get('kind',p.stem)
            if raw.get('schema_version')=='1.0.0':
                supported={'run-manifest','snapshot-manifest','simulation-evidence'}
                if kind not in supported:
                    unknown.append('Native record adapter unsupported: '+kind)
                    continue
                native.append({'kind':kind,'run_id':raw.get('run_id'),'snapshot_id':raw.get('snapshot_id'),
                               'validation':'BOUNDARY_FIELDS_ONLY; full schema/semantic review belongs to installed engineering skill'})
                if not raw.get('run_id') or not raw.get('snapshot_id'): unknown.append('Native run/snapshot identity missing')
                if kind=='run-manifest':
                    for key in ('command','working_directory','tool','evidence_paths'):
                        if not raw.get(key): unknown.append('Native run field missing: '+key)
                    if raw.get('exit_code')!=0: reasons.append('Native run did not exit successfully')
                if kind=='snapshot-manifest' and (not raw.get('source_files') or not raw.get('revision')):
                    unknown.append('Native snapshot input identity incomplete')
                if kind=='simulation-evidence':
                    if raw.get('classification')!='SIMULATION_PASS': reasons.append('Native simulation is not FUNCTIONAL PASS')
                    if any(raw.get(k)!=0 for k in ('compile_exit_code','elaboration_exit_code','run_exit_code')):
                        reasons.append('Native simulation stage failed or is unknown')
                    if raw.get('tests_executed',0)<1 or raw.get('tests_discovered',0)<1 or not raw.get('comparisons'):
                        reasons.append('Native simulation/checker not exercised')
                    if raw.get('scoreboard_drained') is not True: reasons.append('Native scoreboard not drained')
                    canaries=raw.get('negative_canaries',[])
                    if not canaries or any(c.get('detected') is not True for c in canaries): reasons.append('Native canary did not detect injected fault')
                    if not raw.get('proof_packet'): unknown.append('Native proof packet missing')
    run_ids={n['run_id'] for n in native if n['run_id']}
    snapshots={n['snapshot_id'] for n in native if n['snapshot_id']}
    if len(run_ids)>1 or len(snapshots)>1: reasons.append('Native records mix run/snapshot identities')
    if index.get('profile')=='FUNCTIONAL_ACCEPTANCE':
        if index.get('checker_activity',0)<=0: reasons.append('Checker never exercised')
        if index.get('negative_canary')!='DETECTED': unknown.append('Required negative canary unproven')
    if index.get('run_result')!='PASS': reasons.append('Run is not passing')
    if not index.get('independent_basis_ref'): unknown.append('Independent premise review still required')
    status='BLOCKED' if reasons else 'INCONCLUSIVE' if unknown else 'OK'
    return result(status, decision='INVALID' if reasons else 'UNKNOWN' if unknown else 'REUSE_CANDIDATE',
                  reasons=reasons, unknown=unknown, rerun='affected scope only if it resolves an identified uncertainty',
                  technical_approval=False, semantic_correctness='Requires independent member judgement; hashes are insufficient',
                  native_records=native, model_only_change_invalidates_eda=False)

def delivery_gate(facts):
    require_schema(facts)
    blockers=[]
    author=facts.get('author'); reviewers=facts.get('reviews',[])
    head=facts.get('head_commit'); candidate=facts.get('candidate_commit')
    qualified=[]
    if not author: blockers.append('Author identity missing')
    if not head or not re.fullmatch(r'[0-9a-f]{40,64}',head): blockers.append('Exact resolved delivery commit required')
    contributions={str(x).casefold() for x in facts.get('contributors',[])}
    latest={}
    for review in reviewers:
        if review.get('actor'): latest[str(review['actor']).casefold()]=review
    for review in latest.values():
        actor=review.get('actor')
        if actor and actor.casefold()!=str(author).casefold() and actor.casefold() not in contributions and review.get('state')=='APPROVED' and review.get('commit')==head:
            qualified.append(actor)
    if not qualified: blockers.append('No qualified non-author approval for exact head')
    if not head or facts.get('evidence_commit')!=head: blockers.append('Evidence does not bind exact delivery head')
    if not candidate or candidate!=facts.get('tested_candidate_commit'): blockers.append('Current integrated candidate is unverified')
    if facts.get('blocking_findings'): blockers.append('Blocking findings remain')
    if facts.get('required_checks_status')!='PASS': blockers.append('Required checks not all executed and passed')
    if facts.get('needs_board') and not facts.get('board_pass'): blockers.append('Required board evidence missing')
    if facts.get('stage') and not facts.get('system_pass'): blockers.append('System criteria not met')
    if facts.get('artifact_pairing')=='MISMATCH' or facts.get('deployment_identity')=='UNKNOWN' and facts.get('needs_board'):
        blockers.append('Hardware/software artifact or deployment identity unverified')
    authentic=facts.get('_read_from_github_live') is True
    return result('BLOCKED' if blockers else 'INCONCLUSIVE', mechanics_eligible=not blockers,
                  blockers=blockers, qualified_reviewers=sorted(set(qualified)),
                  approval_authenticity='GITHUB_EVENTS_READ' if authentic else 'UNVERIFIED_IMPORTED_FACTS',
                  delivery_approved=False, reason='Local facts never manufacture human approval; verify acceptance scope at authoritative GitHub record',
                  should_close_issue=not blockers and facts.get('full_definition_done') is True and authentic)

def cleanup_plan(root, inventory, config):
    require_schema(inventory)
    layout=_layout(config)
    allowed=layout.get('runtime_roots',{}).get('diagnostics','codex_out')
    view=dependency_view(root,layout)
    protected=layout.get('source_exceptions',[])+config.get('workspace',{}).get('protected_paths',[])+view['files']+view['filelists']
    rows=[]
    for item in inventory.get('items',[]):
        rel=relative(item['path']); p=safe_path(root,rel)
        reasons=[]
        if not contains(allowed,rel) or rel==allowed: reasons.append('Not a bounded diagnostic child')
        if any(contains(v,rel) or contains(rel,v) for v in protected): reasons.append('Protected input overlaps')
        if item.get('owner')!='fpga-team-workflow': reasons.append('Unknown ownership')
        if item.get('regenerable') is not True or not item.get('recipe_ref'): reasons.append('Rebuild not established')
        if item.get('active') is not False: reasons.append('Active or unknown occupancy')
        if item.get('unique_data') is not False or item.get('failed_evidence') is not False: reasons.append('Unique data/failure evidence protection')
        if not p.exists(): reasons.append('Missing path')
        files=tree(p) if p.is_dir() else {rel:file_hash(p)} if p.is_file() else {}
        if view['errors'] or view['unsupported']: reasons.append('Dependency ownership is incomplete')
        if item.get('owned_files')!=files: reasons.append('Unknown or changed files compared to ownership manifest')
        rows.append({'path':rel,'eligible':not reasons,'retain_reasons':reasons,'file_count':len(files),
                     'content_identity':digest(files),'bytes':sum(safe_path(p,x).stat().st_size for x in files) if p.is_dir() else p.stat().st_size if p.is_file() else 0})
    return result(dry_run=True, items=rows, deleted=[], note='Deletion is deliberately not implemented; an eligible plan is not deletion authorization')

def handoff(facts, config, task):
    require_schema(facts)
    rec=recommend(config,task)
    lines=['# 工作包交接', '', f"任务：{task.get('task_ref','UNKNOWN')}；准确版本：{facts.get('head_commit','UNKNOWN')}",
           f"申请范围：{facts.get('scope','UNKNOWN')}", f"实际完成：{facts.get('completed','UNKNOWN')}",
           f"模型建议：{rec['recommended']['model_id']} / {rec['recommended']['reasoning_effort']}；实际设置 UNKNOWN；仅建议",
           f"策略：{rec['policy_version']}；可用性：{rec['availability_status']}；质量：{rec['quality_status']}",
           '复用证据（未重跑）：'+json.dumps(facts.get('reused_evidence',[]),ensure_ascii=False),
           '新增检查：'+json.dumps(facts.get('new_checks',[]),ensure_ascii=False),
           '关键前提独立核对：'+str(facts.get('independent_basis_ref','UNKNOWN')),
           '阻断／未测：'+json.dumps(facts.get('limitations',['UNKNOWN']),ensure_ascii=False),
           '证据入口：'+json.dumps(facts.get('evidence_refs',[]),ensure_ascii=False),
           '成员批准：从真实 review 事件核对；本文不产生批准。']
    return result(markdown='\n\n'.join(lines)+'\n', recommendation=rec, gate=delivery_gate(facts),remote_writes=[])

def doctor(root, config, skill=None, agents=None, target=None):
    require_schema(config)
    issues=[]
    try: layout=inspect_layout(root,config,target)
    except Refusal as exc: layout=result('BLOCKED',error=str(exc))
    if config.get('model_policy'):
        try: validate_policy(config['model_policy'])
        except Refusal as exc: issues.append(str(exc))
    else: issues.append('Model recommendation policy is not configured; current settings preserved')
    dependency=upstream_check(skill,agents) if skill and agents else result('INCONCLUSIVE',reason='Explicit dependency and role roots required')
    lock_ref=config.get('maintenance',{}).get('lock_file','workflow-lock.yaml')
    lock_path=safe_path(root,lock_ref)
    lock_status='UNKNOWN'
    if lock_path.is_file():
        project_lock=read(lock_path)
        try:
            require_schema(project_lock)
            expected=read(PACKAGE/'assets/upstream-lock.json')
            if project_lock.get('engineering_skill',{}).get('source_commit')!=expected['source_commit']:
                issues.append('Project dependency lock differs from supported upstream commit')
            if project_lock.get('engineering_skill',{}).get('version')!=expected['version']:
                issues.append('Project dependency version mismatch')
            if project_lock.get('bridge',{}).get('schema_version')!=1: issues.append('Unsupported bridge schema')
            policy_lock=project_lock.get('model_policy',{})
            if config.get('model_policy') and policy_lock.get('content_sha256') and policy_lock['content_sha256']!=digest(config['model_policy']):
                issues.append('Model policy content differs from project lock')
            release=project_lock.get('outer_skill',{}).get('release')
            if release and release!=(PACKAGE/'VERSION').read_text().strip(): issues.append('Outer release differs from project lock')
            lock_status='CHECKED' if not issues else 'MISMATCH'
        except Refusal as exc: issues.append(str(exc));lock_status='UNSUPPORTED'
    return result('BLOCKED' if issues or layout['status']=='BLOCKED' or dependency['status']=='BLOCKED' else 'INCONCLUSIVE',
                  layout=layout, dependency=dependency, project_lock_status=lock_status, issues=issues,
                  tools={k:shutil.which(k) for k in ('git','gh','vivado','xsim','vsim')},
                  model_actual='UNKNOWN',client_loaded='UNKNOWN',writes=[])
