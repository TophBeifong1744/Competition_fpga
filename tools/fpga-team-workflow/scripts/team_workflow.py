#!/usr/bin/env python3
"""fpga-team-workflow deterministic helper. Default read-only; JSON output and real exit codes."""
from pathlib import Path
import argparse
import sys
sys.dont_write_bytecode=True
from ftw_common import Refusal, emit, guard_main, read, result, run
from model_policy import inspect_settings, recommend
from workflow_ops import (cleanup_plan, delivery_gate, doctor, handoff, init_layout,
                          inspect_layout, snapshot, upstream_check, workspace_apply, workspace_plan, evidence_inspect)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command',choices=['doctor','layout','workspace','snapshot','evidence','handoff','model','cleanup','delivery','upstream'])
    ap.add_argument('action',nargs='?',default='inspect')
    for flag in ('root','config','task','facts','inputs','previous','index','current','evidence-root','occupancy','plan','inventory','metadata','requested','roles','skill','agents','target','destination','capabilities','authorization-ref','out'):
        ap.add_argument('--'+flag)
    ap.add_argument('--execute',action='store_true');ap.add_argument('--dry-run',action='store_true')
    a=ap.parse_args()
    if a.execute and a.dry_run: raise Refusal('Choose --execute or --dry-run')
    if a.execute and not a.authorization_ref: raise Refusal('Existing user authorization reference required')
    load=lambda name: read(getattr(a,name)) if getattr(a,name) else None
    cmd,act=a.command,a.action
    if cmd=='doctor': out=doctor(a.root,load('config'),a.skill,a.agents,a.target)
    elif cmd=='upstream': out=upstream_check(a.skill,a.agents)
    elif cmd=='layout' and act=='inspect': out=inspect_layout(a.root,load('config'),a.target)
    elif cmd=='layout' and act=='init': out=init_layout(a.root,load('config'),a.execute)
    elif cmd=='workspace' and act=='plan': out=workspace_plan(a.root,load('task'),load('config'),load('occupancy'),a.target)
    elif cmd=='workspace' and act=='apply': out=workspace_apply(load('plan'),load('config'),load('occupancy'),a.execute,a.destination)
    elif cmd=='snapshot': out=snapshot(a.root,load('inputs'),load('previous'))
    elif cmd=='evidence': out=evidence_inspect(load('index'),load('current'),a.evidence_root)
    elif cmd=='handoff' and act=='render': out=handoff(load('facts'),load('config'),load('task'))
    elif cmd=='model' and act=='recommend': out=recommend(load('config'),load('task'),load('capabilities'))
    elif cmd=='model' and act=='inspect': out=inspect_settings(load('metadata'), sorted(Path(a.roles).glob('*.toml')) if a.roles else [],load('requested'))
    elif cmd=='model' and act=='apply': out=result('NEEDS_USER_ACTION',application_status='UNSUPPORTED',settings_modified=False,
        manual_path='Desktop model/effort picker or interactive CLI /model; verify actor availability and actual setting separately')
    elif cmd=='cleanup' and act=='plan': out=cleanup_plan(a.root,load('inventory'),load('config'))
    elif cmd=='delivery':
        facts=load('facts')
        facts.pop('_read_from_github_live',None)
        out=delivery_gate(facts)
    else: raise Refusal('Unsupported command/action pair')
    return emit(out,a.out)

if __name__=='__main__': guard_main(main)
