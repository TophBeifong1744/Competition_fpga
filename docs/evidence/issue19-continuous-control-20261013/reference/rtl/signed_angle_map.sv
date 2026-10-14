`timescale 1ns/1ps
`default_nettype none
// S18F8 canonical input; no wrap or clamp. Integer result uses ties-to-even.
module signed_angle_map (
    input wire config_valid,
    input wire signed [17:0] angle_q8,
    input wire signed [23:0] offset_q8,
    input wire signed [1:0] direction,
    input wire signed [17:0] domain_min_q8, domain_max_q8,
    input wire [8:0] mechanical_min, mechanical_max,
    input wire [8:0] servo_max,
    output wire config_legal,
    output wire valid,
    output wire [8:0] angle_deg
);
    localparam signed [25:0] NEG_180_Q8 = -26'sd46080;
    localparam signed [25:0] POS_180_Q8 = 26'sd46080;
    wire signed [25:0] raw = {{8{angle_q8[17]}},angle_q8};
    wire signed [25:0] offset = {{2{offset_q8[23]}},offset_q8};
    wire signed [25:0] mapped = offset + ((direction == -2'sd1) ? -raw : raw);
    wire signed [25:0] min_q8 = $signed({8'd0,mechanical_min,8'd0});
    wire signed [25:0] max_q8 = $signed({8'd0,mechanical_max,8'd0});
    wire [17:0] whole = mapped[25:8];
    wire [7:0] fraction = mapped[7:0];
    wire increment = (fraction > 8'd128) ||
                     ((fraction == 8'd128) && whole[0]);
    wire [18:0] rounded = {1'b0,whole} + {18'd0,increment};
    wire config_good = config_valid &&
        ((direction == 2'sd1) || (direction == -2'sd1)) &&
        domain_min_q8 >= NEG_180_Q8 && domain_max_q8 < POS_180_Q8 &&
        domain_min_q8 <= domain_max_q8 &&
        mechanical_min <= mechanical_max && mechanical_max <= servo_max &&
        servo_max != 9'd0;
    assign config_legal = config_good;
    assign valid = config_good && raw >= NEG_180_Q8 && raw < POS_180_Q8 &&
        raw >= $signed(domain_min_q8) && raw <= $signed(domain_max_q8) &&
        mapped >= min_q8 && mapped <= max_q8 &&
        rounded <= {10'd0,servo_max} && rounded <= 19'd511;
    assign angle_deg = valid ? rounded[8:0] : 9'd0;
endmodule
`default_nettype wire
