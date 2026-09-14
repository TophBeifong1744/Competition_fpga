import pathlib,shutil
ROOT=pathlib.Path(__file__).parent
source=pathlib.Path('F:/NUEC/review-worktrees/b-skl001-c562466/skill/fpga-module-verification/examples/elastic')
dest=ROOT/'latency-mutant';shutil.copytree(source,dest)
old=(source/'elastic_stage.v').read_text()
new=old.replace('module elastic_stage','module inner_stage')+'''
module elastic_stage #(parameter WIDTH=8)(
 input wire clk,rst_n,in_valid,
 input wire [WIDTH-1:0] in_data,
 output wire in_ready,out_valid,
 output wire [WIDTH-1:0] out_data,
 input wire out_ready);
 wire mid_valid,mid_ready;
 wire [WIDTH-1:0] mid_data;
 inner_stage #(.WIDTH(WIDTH)) a(.clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(in_ready),.in_data(in_data),.out_valid(mid_valid),.out_ready(mid_ready),.out_data(mid_data));
 inner_stage #(.WIDTH(WIDTH)) b(.clk(clk),.rst_n(rst_n),.in_valid(mid_valid),.in_ready(mid_ready),.in_data(mid_data),.out_valid(out_valid),.out_ready(out_ready),.out_data(out_data));
endmodule
'''
(dest/'elastic_stage.v').write_text(new)
