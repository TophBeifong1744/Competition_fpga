`timescale 1ns/1ps
// Independent contract checker: literal expected widths; no DUT arithmetic reused.
module servo_top_case #(
    parameter integer ID=0, H=180, V=130, H_US=1500, V_US=1682
)(input wire clk, output reg done=0);
    wire hp, vp;
    servo_dual_test_top #(.HORIZONTAL_DEG(H), .VERTICAL_DEG(V)) dut
        (.sys_clk(clk), .pwm_horizontal(hp), .pwm_vertical(vp));
    integer cycle=0, valid_samples=0, checks=0;
    integer start_edge, period_cycles, width_h, width_v, offset_cycles, frame;
    integer valid_edge;
    reg sampled_valid, expected_h, expected_v, prev_h=0, prev_v=0;
    reg neg_width, neg_period, neg_startup, neg_valid;
    initial begin
        neg_width=(ID==0) && $test$plusargs("NEG_WIDTH");
        neg_period=(ID==0) && $test$plusargs("NEG_PERIOD");
        neg_startup=(ID==0) && $test$plusargs("NEG_STARTUP");
        neg_valid=(ID==0) && $test$plusargs("NEG_VALID");
        start_edge=17+(neg_startup ? 1:0);
        period_cycles=1000000+(neg_period ? 1:0);
        valid_edge=17+(neg_valid ? 1:0);
    end
    always @(posedge clk) begin
        cycle=cycle+1;
        // Sample command acceptance on the edge, before NBA; outputs after NBA.
        sampled_valid=dut.command_valid;
        #1;
        if (!done) begin
            checks=checks+1;
            if (sampled_valid !== (cycle==valid_edge)) begin
                $display("COMPARE tag=valid case=%0d accepted_cycle=17 expected_cycle=%0d observed_cycle=%0d result=FAIL ASSERTION_FAIL",ID,valid_edge,cycle);
                $fatal(1,"CHECKER_FAIL valid");
            end
            if (sampled_valid) begin
                valid_samples=valid_samples+1;
                $display("COMPARE tag=valid case=%0d accepted_cycle=17 expected_cycle=17 observed_cycle=%0d result=PASS",ID,cycle);
            end
            expected_h=0; expected_v=0;
            frame=-1;
            if (cycle>=start_edge) begin
                frame=(cycle-start_edge)/period_cycles;
                offset_cycles=(cycle-start_edge)%period_cycles;
                width_h=(frame==0 ? 1500:H_US)*50;
                width_v=(frame==0 ? 1682:V_US)*50;
                if (neg_width && frame==0) width_h=width_h+50;
                expected_h=(offset_cycles<width_h);
                expected_v=(offset_cycles<width_v);
            end
            checks=checks+2;
            if (hp !== expected_h || vp !== expected_v) begin
                $display("COMPARE tag=pwm case=%0d frame=%0d accepted_cycle=17 expected_cycle=%0d observed_cycle=%0d expected_h=%0b observed_h=%0b expected_v=%0b observed_v=%0b result=FAIL ASSERTION_FAIL",ID,frame,cycle,cycle,expected_h,hp,expected_v,vp);
                $fatal(1,"CHECKER_FAIL pwm width/period/startup");
            end
            if (hp !== prev_h)
                $display("COMPARE tag=H_edge case=%0d frame=%0d accepted_cycle=17 expected_cycle=%0d observed_cycle=%0d level=%0b result=PASS",ID,frame,start_edge+frame*period_cycles+(hp ? 0:width_h),cycle,hp);
            if (vp !== prev_v)
                $display("COMPARE tag=V_edge case=%0d frame=%0d accepted_cycle=17 expected_cycle=%0d observed_cycle=%0d level=%0b result=PASS",ID,frame,start_edge+frame*period_cycles+(vp ? 0:width_v),cycle,vp);
            prev_h=hp; prev_v=vp;
            if (cycle==3000017) begin
                if (valid_samples!=1) $fatal(1,"CHECKER_FAIL duplicate/drop valid");
                done=1;
                $display("CASE_PASS case=%0d H=%0d V=%0d expected_H_us=%0d expected_V_us=%0d checks=%0d valid_count=%0d drain=COMPLETE",ID,H,V,H_US,V_US,checks,valid_samples);
            end
        end
    end
endmodule

module tb_servo_dual_test_top;
    reg clk=0;
    always #10 clk=~clk;
    wire [5:0] done;
    servo_top_case #(.ID(0)) c0(clk,done[0]);
    servo_top_case #(.ID(1),.H(-1),.V(-1),.H_US(500),.V_US(864)) c1(clk,done[1]);
    servo_top_case #(.ID(2),.H(1024),.V(1024),.H_US(2500),.V_US(2500)) c2(clk,done[2]);
    servo_top_case #(.ID(3),.H(90),.V(55),.H_US(1000),.V_US(1000)) c3(clk,done[3]);
    servo_top_case #(.ID(4),.H(360),.H_US(2500)) c4(clk,done[4]);
    servo_top_case #(.ID(5),.V(220),.V_US(2500)) c5(clk,done[5]);
    initial begin
        wait (&done);
        $display("TEST_PASS cases=6 clock_hz=50000000 cycles=3000017 checks=54000306 seed=19");
        $finish;
    end
    initial begin
        #60001000;
        $fatal(1,"TIMEOUT_HANG checker drain incomplete");
    end
endmodule
