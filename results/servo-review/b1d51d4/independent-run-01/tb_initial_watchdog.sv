`timescale 1ns/1ps
module tb_independent;
  parameter integer CLK_FREQ_HZ=1000000;
  localparam integer CPM=CLK_FREQ_HZ/1000000;
  localparam integer PERIOD=20000*CPM;
  localparam real HALF=500000000.0/CLK_FREQ_HZ;
  reg clk=0, rst_n=0;
  reg [8:0] angle=0;
  wire pwm;
  integer checks=0, frames=0, n, k;
  integer phase=0, width=0;
  bit started=0;
  real scaled;
  motor_drive #(.CLK_FREQ_HZ(CLK_FREQ_HZ)) dut(clk,rst_n,angle,pwm);
  always #(HALF) clk=~clk;
  // Independent real-valued golden, cycle-by-cycle port oracle, no internal probes.
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      started=0; phase=0; width=0;
      #0.002;
      if (pwm !== 1'b0) $fatal(1,"reset did not pull low");
    end else begin
      if (!started || phase==PERIOD-1) begin
        phase=0; started=1;
        scaled=500.0+((angle>360 ? 360 : angle)*2000.0/360.0);
        width=$rtoi(scaled+0.5)*CPM;
        frames=frames+1;
      end else phase=phase+1;
      #0.002;
      if (pwm !== (phase<width))
        $fatal(1,"port mismatch frame=%0d phase=%0d angle=%0d width=%0d pwm=%b",frames,phase,angle,width,pwm);
      checks=checks+1;
    end
  end
  task restart(input integer value);
    @(negedge clk); rst_n=0; angle=value;
    repeat(3) @(negedge clk);
    rst_n=1;
  endtask
  initial begin
    // All input encodings, complete frames without restarting between commands.
    restart(0);
    for(n=0;n<512;n=n+1) begin
      angle=n;
      repeat(PERIOD) @(negedge clk);
    end
    // Multiple commands per frame: near boundary, while high, while low.
    for(k=0;k<3;k=k+1) begin
      angle=0;
      repeat(10*CPM) @(negedge clk); angle=360;
      repeat(3000*CPM) @(negedge clk); angle=90;
      repeat(PERIOD-3010*CPM-1) @(negedge clk); angle=359;
      @(negedge clk);
    end
    // Deliberately asynchronous assertion while high; synchronous-safe release.
    restart(360);
    repeat(20) @(negedge clk);
    #(HALF/3.0); rst_n=0;
    repeat(3) @(negedge clk); angle=180; rst_n=1;
    repeat(PERIOD) @(negedge clk);
    // Reset in low phase followed by complete restart.
    repeat(3000*CPM) @(negedge clk);
    #(HALF/3.0); rst_n=0;
    repeat(3) @(negedge clk); angle=1; rst_n=1;
    repeat(PERIOD) @(negedge clk);
    $display("PASS independent angles=512 frames=%0d cycle_checks=%0d CLK_FREQ_HZ=%0d",frames,checks,CLK_FREQ_HZ);
    $finish;
  end
  initial begin #11000000000; $fatal(1,"independent watchdog timeout"); end
endmodule
