`timescale 1ns/1ps
// 每bin复用同一算术核；ROM、两次Newton及最终RNE与旧数学定义一致。
module doa_phat_serial (
  input logic clk,cold_rst_n,cancel,start,
  output logic ready,done,
  input logic signed [50:0] in_real,in_imag,
  input logic [191:0] in_square,
  output logic [51:0] result,
  output logic busy
);
  import doa_math_pkg::*;
  logic [3:0] stage;
  logic issued;
  wide_t re,im,mag,mant,r,mr,temp,out_re;
  integer exponent,leading,rom_index,i;
  logic alu_start,alu_ready,alu_done,alu_busy;
  logic [1:0] alu_op;
  wide_t alu_a,alu_b,alu_result;
  logic signed [31:0] alu_shift;
  assign ready=!busy;
  doa_math_serial math(.clk(clk),.cold_rst_n(cold_rst_n),.cancel(cancel),
    .start(alu_start),.ready(alu_ready),.operation(alu_op),.operand_a(alu_a),
    .operand_b(alu_b),.shift(alu_shift),.done(alu_done),.result(alu_result),.busy(alu_busy));
  always_comb begin
    leading=0;
    for(i=0;i<96;i=i+1) if(mag[i]) leading=i;
    rom_index=(mant-(192'sd1<<30))>>>22;
    if(rom_index<0) rom_index=0;if(rom_index>255) rom_index=255;
    alu_start=busy && !issued && alu_ready && !cancel;
    alu_op=2;alu_a=temp;alu_b=0;alu_shift=30;
    case(stage)
      0: begin alu_op=1;alu_a=temp;end
      1: begin alu_a=mag;alu_shift=leading-30;end
      2: begin alu_op=3;alu_a=mant;alu_b=wide_t'($unsigned(recip_rom(rom_index[7:0])));end
      6: begin alu_op=3;alu_a=mant;alu_b=r;end
      3,7: begin alu_a=temp;end
      4,8: begin alu_op=3;alu_a=r;alu_b=(192'sd2<<30)-mr;end
      5,9: begin alu_a=temp;end
      10: begin alu_op=3;alu_a=re;alu_b=r;end
      11: begin alu_a=temp;alu_shift=exponent-17;end
      12: begin alu_op=3;alu_a=im;alu_b=r;end
      13: begin alu_a=temp;alu_shift=exponent-17;end
      default: begin alu_start=0;end
    endcase
  end
  always_ff @(posedge clk) begin
    if(!cold_rst_n || cancel) begin
      busy<=0;done<=0;result<=0;stage<=0;issued<=0;
      re<=0;im<=0;mag<=0;mant<=0;r<=0;mr<=0;temp<=0;out_re<=0;exponent<=0;
    end else begin
      done<=0;
      if(start && ready) begin
        result<=0;re<=wide_t'(in_real);im<=wide_t'(in_imag);
        temp<=in_square<<48;stage<=0;issued<=0;
        if(in_square==0) begin result<=52'h8000000000000;done<=1;busy<=0;end
        else busy<=1;
      end else if(busy) begin
        if(alu_start) issued<=1;
        if(alu_done) begin
          issued<=0;stage<=stage+1;
          case(stage)
            0: mag<=alu_result;
            1: begin mant<=alu_result;exponent<=leading;end
            // ROM seed is selected from newly published mant at stage2 issue.
            2,4,6,8,10,12: temp<=alu_result;
            3,7: mr<=alu_result;
            5,9: r<=alu_result;
            11: out_re<=alu_result;
            13: begin
              result<=0;
              if(out_re< -192'sd16777216 || out_re>192'sd16777215 ||
                 alu_result< -192'sd16777216 || alu_result>192'sd16777215) result[51]<=1;
              else begin result[49:25]<=out_re[24:0];result[24:0]<=alu_result[24:0];end
              busy<=0;done<=1;
            end
          endcase
        end
        if(stage==2 && !issued) r<=wide_t'($unsigned(recip_rom(rom_index[7:0])));
      end
    end
  end
endmodule
