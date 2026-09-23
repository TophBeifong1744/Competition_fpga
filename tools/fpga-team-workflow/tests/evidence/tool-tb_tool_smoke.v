// Standalone tool-entry diagnostic fixture, not a product or functional-acceptance TB.
module tb_tool_smoke;
  initial begin
    $display("FTW_TOOL_SMOKE_STARTED");
    #1;
    $display("FTW_TOOL_SMOKE_COMPLETED");
    $finish;
  end
endmodule
