module sat_add(input wire clk, input wire rst,
 input wire in_valid, output wire in_ready,
 input wire signed [7:0] a,b,
 output reg out_valid, input wire out_ready,
 output reg signed [7:0] y);
 wire signed [8:0] wide_sum = {a[7],a}+{b[7],b};
 assign in_ready = !out_valid || out_ready;
 always @(posedge clk) begin
  if (rst) begin out_valid<=0; y<=0; end
  else if(in_ready) begin
   out_valid<=in_valid;
   if(in_valid) begin
    if(wide_sum > 9'sd127) y<=8'sd127;
    else if(wide_sum < -9'sd128) y<=8'bxxxxxxxx;
    else y<=wide_sum[7:0];
   end
  end
 end
endmodule
