`timescale 1ns/1ps
// 复用192位整数运算；取消清除局部请求，不声称硬件IP退休。
module doa_math_serial (
  input logic clk, cold_rst_n, cancel,
  input logic start, output logic ready,
  input logic [1:0] operation, // 0=RNE DIV,1=RNE SQRT,2=RNE SHIFT,3=MUL low192
  input logic signed [191:0] operand_a, operand_b,
  input logic signed [31:0] shift,
  output logic done, output logic signed [191:0] result,
  output logic busy
);
  logic [1:0] op;
  logic [191:0] a,d,q,remn,mul_a,mul_b,acc;
  logic [95:0] root;
  logic [193:0] sqrt_rem;
  logic [7:0] count;
  logic negative,left_shift,sticky;
  logic [192:0] div_trial;
  logic [191:0] div_next_q,div_next_rem,rounded_q;
  logic [193:0] sqrt_trial,sqrt_divisor,sqrt_next_rem;
  logic [95:0] sqrt_next_root;
  logic [191:0] shift_next,shift_rounded,mul_next;
  logic [191:0] input_magnitude;
  integer dividend_bits,bit_index;
  assign ready=!busy;
  always_comb begin
    input_magnitude=operand_a<0 ? -operand_a : operand_a;
    dividend_bits=1;
    for(bit_index=0;bit_index<192;bit_index=bit_index+1)
      if(input_magnitude[bit_index]) dividend_bits=bit_index+1;
    // 前导零不参与恢复除法；选择下一原始位，不构造宽可变移位器。
    div_trial={remn,(count!=0 ? a[count-1] : 1'b0)};
    div_next_q={q[190:0],1'b0};
    div_next_rem=div_trial[191:0];
    if(div_trial>={1'b0,d}) begin
      div_next_rem=div_trial-{1'b0,d};div_next_q[0]=1;
    end
    // 原函数(r<<1)在192位截断；保留原精度与ties-to-even。
    rounded_q=q;
    if((remn<<1)>d || ((remn<<1)==d && q[0])) rounded_q=q+1;
    sqrt_trial=(sqrt_rem<<2)|{192'd0,a[191:190]};
    sqrt_divisor=({98'd0,root}<<2)|194'd1;
    sqrt_next_rem=sqrt_trial;
    sqrt_next_root={root[94:0],1'b0};
    if(sqrt_trial>=sqrt_divisor) begin
      sqrt_next_rem=sqrt_trial-sqrt_divisor;sqrt_next_root[0]=1;
    end
    shift_next=left_shift ? (a<<1) : (a>>1);
    shift_rounded=shift_next;
    if(!left_shift && a[0] && (sticky || shift_next[0])) shift_rounded=shift_next+1;
    mul_next=acc+(mul_b[0] ? mul_a : 192'd0);
  end
  always_ff @(posedge clk) begin
    if(!cold_rst_n || cancel) begin
      busy<=0;done<=0;result<=0;op<=0;a<=0;d<=0;q<=0;remn<=0;
      root<=0;sqrt_rem<=0;count<=0;negative<=0;left_shift<=0;sticky<=0;
      mul_a<=0;mul_b<=0;acc<=0;
    end else begin
      done<=0;
      if(start && ready) begin
        busy<=1;op<=operation;count<=0;negative<=operand_a<0;
        q<=0;remn<=0;root<=0;sqrt_rem<=0;sticky<=0;acc<=0;
        d<=operand_b;a<=operand_a;
        mul_a<=operand_a;mul_b<=operand_b;
        case(operation)
          0: begin a<=input_magnitude;count<=dividend_bits;end
          1: count<=96;
          2: begin
            left_shift<=shift<0;
            a<=shift<0 ? operand_a : (operand_a<0 ? -operand_a : operand_a);
            // 正移位191时原除数为负；超宽移位结果亦为零。
            if((shift>=191) || (shift<=-192)) begin a<=0;count<=0;end
            else count<=shift<0 ? -shift : shift;
          end
          3: count<=192;
        endcase
      end else if(busy) begin
        case(op)
          0: if($signed(d)<=0) begin result<=0;busy<=0;done<=1;end
             else if(count!=0) begin
               q<=div_next_q;remn<=div_next_rem;count<=count-1;
             end else begin
               result<=negative ? -$signed(rounded_q) : $signed(rounded_q);busy<=0;done<=1;
             end
          1: if(count!=0) begin
               a<=a<<2;root<=sqrt_next_root;sqrt_rem<=sqrt_next_rem;count<=count-1;
             end else begin
               // n-q*q>q 等价于4*n>(2*q+1)^2，无试平方乘法。
               result<={96'd0,(root+(sqrt_rem>{98'd0,root} ? 96'd1 : 96'd0))};
               busy<=0;done<=1;
             end
          2: if(count==0) begin
               result<=left_shift ? $signed(a) : (negative ? -$signed(a) : $signed(a));busy<=0;done<=1;
             end else if(count==1) begin
               result<=left_shift ? $signed(shift_next) : (negative ? -$signed(shift_rounded) : $signed(shift_rounded));
               busy<=0;done<=1;count<=0;
             end else begin a<=shift_next;sticky<=sticky|a[0];count<=count-1;end
          3: begin
               mul_a<=mul_a<<1;mul_b<=mul_b>>1;acc<=mul_next;count<=count-1;
               // 后续乘数位全零时已精确完成；负数仍需完整192位。
               if(count==1 || mul_b[191:1]==0) begin result<=mul_next;busy<=0;done<=1;end
             end
        endcase
      end
    end
  end
endmodule
