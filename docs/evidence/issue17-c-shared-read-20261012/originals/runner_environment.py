import pathlib,os
TOOLS=pathlib.Path('C:/AMDDesignTools/2025.2/Vivado')
env=os.environ.copy();env['PROCESSOR_ARCHITECTURE']='AMD64'
env.update(XILINX_VIVADO=str(TOOLS),RDI_APPROOT=str(TOOLS),HDI_APPROOT=str(TOOLS),RDI_OPT_EXT='.o',RDI_DATADIR=str(TOOLS/'data'),RDI_LIBDIR=str(TOOLS/'lib/win64.o'),RDI_BINDIR=str(TOOLS/'bin'),RDI_PLATFORM='win64',TCL_LIBRARY=str(TOOLS.parent/'tps/tcl/tcl8.6'))
env['PATH']=';'.join(str(p) for p in [TOOLS/'lib/win64.o',TOOLS/'lib/win64.o/Default',TOOLS/'bin/unwrapped/win64.o',*[TOOLS.parent/p for p in ['tps/win64/jre21.0.5_11/bin/server','tps/win64/jre21.0.5_11/bin','tps/win64/python-3.13.0','tps/mingw/6.2.0/win64.o/nt/bin']]])+';'+env['PATH']
