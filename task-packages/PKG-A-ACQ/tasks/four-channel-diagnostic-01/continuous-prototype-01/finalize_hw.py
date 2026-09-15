"""Finish hardware-only XSA after a successful direct bitgen, WITHOUT rerouting.
Only a fresh copy of the previous candidate project is opened; retain failure.
"""
import argparse,json,os,shutil
from pathlib import Path
import xml.etree.ElementTree as ET
import run as c
p=argparse.ArgumentParser();p.add_argument('--built',required=True);p.add_argument('--output',required=True);a=p.parse_args()
old=c.safe.no_links(a.built);out=c.fresh(a.output)
try:
    plan=json.loads((old/'preflight.json').read_text())
    log=(old/'logs/vivado.log').read_text()
    c.safe.require('Bitgen Completed Successfully' in log,'no real bitgen evidence')
    timing=c.safe.timing_summary_values((old/'reports/timing-summary.rpt').read_text())
    c.safe.require(all(v>=0 for v in timing.values()),'timing fails')
    project=out/'project';shutil.copytree(old/'inputs/project',project)
    xpr=project/'one.xpr';tree=ET.parse(xpr);tree.getroot().set('Path',xpr.as_posix());tree.write(xpr,encoding='UTF-8',xml_declaration=True)
    env=json.loads((old/'tool-environment.json').read_text());os.environ['TCLLIBPATH']=env['TCLLIBPATH']
    script='''if {[version -short] ne "2025.2"} {error "wrong version"}
open_project [file join [pwd] project one.xpr]
write_hw_platform -fixed [file join [pwd] system_continuous.xsa]
close_project
puts "HARDWARE_ONLY_XSA_EXPORTED_NO_NEW_SYNTH_OR_ROUTE"
'''
    (out/'export.tcl').write_text(script,encoding='utf-8')
    c.run([plan['vivado'],'-mode','batch','-source','export.tcl','-log','vivado-export.log','-nojournal'],out,'export')
    base=c.driver_binding(old/'inputs/bsp-reference.xsa');new=c.driver_binding(out/'system_continuous.xsa')
    c.write(out/'bsp-binding.json',{'baseline':base,'candidate':new,'equal':base==new})
    c.safe.require(base==new,'BSP configuration changed')
    c.safe.require(not c.safe.unchanged(plan),'original one/BSP/PS changed')
    c.write(out/'result.json',{'status':'FINALIZED_BUILD_NOT_BOARD','hardware_build':str(old),'timing':timing,'XSA_includes_bit':False,
         'external_bit_sha256':c.safe.sha(old/'artifacts/hw/system_continuous.bit'),'BSP_match':True,'original_unchanged':True})
except Exception as e:
    c.write(out/'failure.json',{'error':str(e)});raise
finally:c.manifest(out)
