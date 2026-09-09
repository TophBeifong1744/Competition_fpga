module start_pulse (
    input  wire aclk,
    input  wire aresetn,
    input  wire start_level,
    output reg  start
);

    reg start_level_d;

    always @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            start_level_d <= 1'b0;
            start         <= 1'b0;
        end else begin
            start_level_d <= start_level;
            start         <= start_level & ~start_level_d;
        end
    end

endmodule