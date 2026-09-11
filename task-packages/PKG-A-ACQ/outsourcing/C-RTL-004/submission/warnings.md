# 警告逐项登记
每项保留原文件和行号；未过滤或抑制工具警告。

- `logs/attempt-bd02/bd.log:56` — WARNING: [IP_Flow 19-5661] Bus Interface 'clk' does not have any bus interfaces associated with it.
  说明：模块只有标量控制/计数端口，没有AXI等数据总线可关联到clk；不新增总线来消警。
- `logs/attempt-bd02/bd.log:57` — WARNING: [IP_Flow 19-11770] Clock interface 'clk' has no FREQ_HZ parameter.
  说明：未声明FREQ_HZ；本包没有正式板上时钟合同，禁止用TB频率代替。
- `logs/attempt-bd02/bd.log:100` — WARNING: [BD 41-2925] The design that will be created by this Tcl script contains the following module references: stream_error_stats_bd.
  说明：导出的BD Tcl依赖已有RTL源；主重建脚本会先导入SV核心和Verilog包装。
- `logs/bd-final/bd.log:55` — WARNING: [IP_Flow 19-5661] Bus Interface 'clk' does not have any bus interfaces associated with it.
  说明：模块只有标量控制/计数端口，没有AXI等数据总线可关联到clk；不新增总线来消警。
- `logs/bd-final/bd.log:56` — WARNING: [IP_Flow 19-11770] Clock interface 'clk' has no FREQ_HZ parameter.
  说明：未声明FREQ_HZ；本包没有正式板上时钟合同，禁止用TB频率代替。
- `logs/bd-final/bd.log:99` — WARNING: [BD 41-2925] The design that will be created by this Tcl script contains the following module references: stream_error_stats_bd.
  说明：导出的BD Tcl依赖已有RTL源；主重建脚本会先导入SV核心和Verilog包装。
- `logs/bd-final/bd.log:114` — WARNING: [BD 41-2925] The design that will be created by this Tcl script contains the following module references: stream_error_stats_bd.
  说明：导出的BD Tcl依赖已有RTL源；主重建脚本会先导入SV核心和Verilog包装。
- `logs/diagnostic/diagnostic.log:28` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:emb-plus-vpr-4616:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\emb-plus-vpr-4616\1.0\board.xml as part xcve2302-sfva784-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:29` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:emb-plus-vpr-4616:part0:1.1 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\emb-plus-vpr-4616\1.1\board.xml as part xcve2302-sfva784-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:30` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:kc705:part0:1.6 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\kc705\1.6\board.xml as part xc7k325tffg900-2 specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:31` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:kc705:part0:1.7 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\kc705\1.7\board.xml as part xc7k325tffg900-2 specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:32` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:kcu105:part0:1.6 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\kcu105\1.6\board.xml as part xcku040-ffva1156-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:33` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:kcu105:part0:1.7 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\kcu105\1.7\board.xml as part xcku040-ffva1156-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:34` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:kcu116:part0:1.4 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\kcu116\1.4\board.xml as part xcku5p-ffvb676-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:35` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:kcu116:part0:1.5 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\kcu116\1.5\board.xml as part xcku5p-ffvb676-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:36` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:kcu1500:part0:1.2 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\kcu1500\1.2\board.xml as part xcku115-flvb2104-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:37` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:scu35:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\scu35\1.0\board.xml as part xcsu35p-sbvb625-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:38` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:v80:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\v80\1.0\board.xml as part xcv80-lsva4737-2mhp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:39` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vc707:part0:1.4 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vc707\1.4\board.xml as part xc7vx485tffg1761-2 specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:40` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vc707:part0:1.5 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vc707\1.5\board.xml as part xc7vx485tffg1761-2 specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:41` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vc709:part0:1.8 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vc709\1.8\board.xml as part xc7vx690tffg1761-2 specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:42` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vck190:part0:2.2 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vck190\production\2.2\board.xml as part xcvc1902-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:43` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vck190:part0:3.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vck190\production\3.0\board.xml as part xcvc1902-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:44` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vck190:part0:3.1 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vck190\production\3.1\board.xml as part xcvc1902-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:45` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vck190:part0:3.2 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vck190\production\3.2\board.xml as part xcvc1902-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:46` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vck190:part0:3.3 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vck190\production\3.3\board.xml as part xcvc1902-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:47` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vck190:part0:3.4 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vck190\production\3.4\board.xml as part xcvc1902-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:48` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vck190_newl:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vck190_newl\production\1.0\board.xml as part xcvc1902-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:49` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vck190_newl:part0:1.1 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vck190_newl\production\1.1\board.xml as part xcvc1902-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:50` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vck190_newl:part0:1.2 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vck190_newl\production\1.2\board.xml as part xcvc1902-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:51` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vck190_newl:part0:1.3 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vck190_newl\production\1.3\board.xml as part xcvc1902-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:52` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vcu108:part0:1.6 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vcu108\1.6\board.xml as part xcvu095-ffva2104-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:53` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vcu108:part0:1.7 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vcu108\1.7\board.xml as part xcvu095-ffva2104-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:54` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vcu110:part0:1.4 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vcu110\1.4\board.xml as part xcvu190-flgc2104-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:55` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vcu118:part0:2.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vcu118\2.0\board.xml as part xcvu9p-flga2104-2l-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:56` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vcu118:part0:2.3 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vcu118\2.3\board.xml as part xcvu9p-flga2104-2l-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:57` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vcu118:part0:2.4 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vcu118\2.4\board.xml as part xcvu9p-flga2104-2l-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:58` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vcu128:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vcu128\production\1.0\board.xml as part xcvu37p-fsvh2892-2l-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:59` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vcu129:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vcu129\production\1.0\board.xml as part xcvu29p-fsga2577-2l-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:60` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vcu1525:part0:1.3 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vcu1525\1.3\board.xml as part xcvu9p-fsgd2104-2l-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:61` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vek280:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vek280\production\1.0\board.xml as part xcve2802-vsvh1760-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:62` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vek280:part0:1.1 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vek280\production\1.1\board.xml as part xcve2802-vsvh1760-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:63` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vek280:part0:1.2 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vek280\production\1.2\board.xml as part xcve2802-vsvh1760-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:64` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vek385:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vek385\1.0\board.xml as part xc2ve3858-ssva2112-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:65` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vek385:part0:1.1 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vek385\1.1\board.xml as part xc2ve3858-ssva2112-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:66` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vek385_1:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vek385_2\1.0\board.xml as part xc2ve3858-ssva2112-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:67` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vermeo_t1_mpsoc:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vermeo_t1_mpsoc\1.0\board.xml as part xczu19eg-ffvd1760-2l-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:68` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vermeo_t1_rfsoc:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vermeo_t1_rfsoc\1.0\board.xml as part xczu21dr-ffvd1156-2l-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:69` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vhk158:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vhk158\production\1.0\board.xml as part xcvh1582-vsva3697-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:70` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vhk158:part0:1.1 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vhk158\production\1.1\board.xml as part xcvh1582-vsva3697-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:71` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vhk158:part0:1.2 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vhk158\production\1.2\board.xml as part xcvh1582-vsva3697-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:72` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vmk180:part0:2.2 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vmk180\production\2.2\board.xml as part xcvm1802-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:73` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vmk180:part0:3.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vmk180\production\3.0\board.xml as part xcvm1802-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:74` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vmk180:part0:3.1 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vmk180\production\3.1\board.xml as part xcvm1802-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:75` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vmk180:part0:3.2 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vmk180\production\3.2\board.xml as part xcvm1802-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:76` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vmk180:part0:3.3 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vmk180\production\3.3\board.xml as part xcvm1802-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:77` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vmk180_newl:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vmk180_newl\production\1.0\board.xml as part xcvm1802-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:78` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vmk180_newl:part0:1.1 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vmk180_newl\production\1.1\board.xml as part xcvm1802-vsva2197-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:79` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vpk120:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vpk120\production\1.0\board.xml as part xcvp1202-vsva2785-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:80` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vpk120:part0:1.1 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vpk120\production\1.1\board.xml as part xcvp1202-vsva2785-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:81` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vpk120:part0:1.2 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vpk120\production\1.2\board.xml as part xcvp1202-vsva2785-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:82` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vpk180:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vpk180\production\1.0\board.xml as part xcvp1802-lsvc4072-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:83` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vpk180:part0:1.1 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vpk180\production\1.1\board.xml as part xcvp1802-lsvc4072-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:84` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vpk180:part0:1.2 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vpk180\production\1.2\board.xml as part xcvp1802-lsvc4072-2mp-e-s specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:85` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vrk160:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vrk160\1.0\board.xml as part xcvr1602-vsva2488-2mp-e-s-es1 specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:86` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:vrk160:part0:1.1 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\vrk160\1.1\board.xml as part xcvr1602-vsva2488-2mp-e-s-es1 specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:87` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:zc706:part0:1.4 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\zc706\1.4\board.xml as part xc7z045ffg900-2 specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:88` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:zc706:part0:1.5 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\zc706\1.5\board.xml as part xc7z045ffg900-2 specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:89` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:zcu102:part0:3.3 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\zcu102\3.3\board.xml as part xczu9eg-ffvb1156-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:90` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:zcu102:part0:3.4 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\zcu102\3.4\board.xml as part xczu9eg-ffvb1156-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:91` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:zcu111:part0:1.2 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\zcu111\1.2\board.xml as part xczu28dr-ffvg1517-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:92` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:zcu111:part0:1.3 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\zcu111\1.3\board.xml as part xczu28dr-ffvg1517-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:93` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:zcu111:part0:1.4 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\zcu111\1.4\board.xml as part xczu28dr-ffvg1517-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:94` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:zcu1275:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\zcu1275\1.0\board.xml as part xczu29dr-ffvf1760-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:95` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:zcu1285:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\zcu1285\1.0\board.xml as part xczu39dr-ffvf1760-2-i specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:96` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:zcu208:part0:2.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\zcu208\production\2.0\board.xml as part xczu48dr-fsvg1517-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:97` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:zcu208ld:part0:2.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\zcu208ld\production\2.0\board.xml as part xczu58dr-fsvg1517-2-i specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:98` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:zcu216:part0:2.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\zcu216\production\2.0\board.xml as part xczu49dr-ffvf1760-2-e specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:99` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:zcu216ld:part0:2.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\zcu216ld\production\2.0\board.xml as part xczu59dr-ffvf1760-2-i specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:100` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:zcu670:part0:2.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\zcu670\2.0\board.xml as part xczu67dr-fsve1156-2-i specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:101` — WARNING: [Board 49-26] cannot add Board Part xilinx.com:zcu670ld:part0:1.0 available at C:/AMDDesignTools/2025.2/data/xhub/boards\XilinxBoardStore\boards\Xilinx\zcu670ld\1.0\board.xml as part xczu57dr-fsve1156-2-i specified in board_part file is either invalid or not available
  说明：诊断重开工程时扫描其他开发板，安装中缺少其对应器件；本工程使用明确的xc7z020clg400-2，不使用这些Board Part。
- `logs/diagnostic/diagnostic.log:102` — WARNING: [Project 1-5713] Board part '' set for the project  is not found. BoardPart property will be unset. Please select board from latest repo build
  说明：诊断工程没有选择Board Part，按具体器件创建；不影响本包器件选择。

## 004-R2：2026-09-11 BD成功运行补充

证据目录：logs/rework_01_20260911_194059。默认32位和修改3位的端口检查及Validate通过，退出码0。
此前appinit初始化失败根因尚未确定；本次成功运行不代表已修复全局TclStore环境。
历史警告保留。以下逐条登记本次日志中的警告原文及行号；通过不等于无警告，仍待B复核批准。

- `logs/rework_01_20260911_194059/bd.log:55` — WARNING: [IP_Flow 19-5661] Bus Interface 'clk' does not have any bus interfaces associated with it.
- `logs/rework_01_20260911_194059/bd.log:56` — WARNING: [IP_Flow 19-11770] Clock interface 'clk' has no FREQ_HZ parameter.
- `logs/rework_01_20260911_194059/bd.log:99` — WARNING: [BD 41-2925] The design that will be created by this Tcl script contains the following module references: stream_error_stats_bd.
- `logs/rework_01_20260911_194059/bd.log:114` — WARNING: [BD 41-2925] The design that will be created by this Tcl script contains the following module references: stream_error_stats_bd.
