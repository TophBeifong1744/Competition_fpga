"""Optional A-machine READ ONLY link enumeration/ELF check; no gate/load/build."""
import json
from pathlib import Path
import sys
entry=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(entry))
import check_entry as gate
out=Path(sys.argv[1]).resolve()
out.mkdir(parents=True,exist_ok=False)
app=Path(gate.POLICY['reference_app'])
bsp=Path(gate.POLICY['reference_bsp'])
ninja=Path('F:/AMD/2025.2/Vitis/bin/ninja.exe')
text=gate.safe.run_command([ninja,'-C',app/'build','-t','commands',app.name+'.elf'],out,'ninja-commands',app)
link=gate.verify_link_output(text,app,bsp)
result=gate.verify_elf(app/'build/CMakeFiles'/f'{app.name}.elf.dir/main.c.obj',app/'build'/f'{app.name}.elf')
gate.safe.write_json(out/'result.json',dict(status='LIVE_READONLY_LINK_ELF_PASS_NOT_LOAD_OR_BUILD',
    link_argv=link,compiled=result,deployment='SHARED_OLD_ENTRY_NOT_REPLACED'))
print('LIVE_READONLY_LINK_ELF_PASS_NOT_LOAD_OR_BUILD')
