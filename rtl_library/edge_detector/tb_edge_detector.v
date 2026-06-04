`timescale 1ns/1ps
module tb_edge_detector;
    reg clk, rst_n, in;
    wire rise;

    edge_detector dut(.clk(clk), .rst_n(rst_n), .in(in), .rise(rise));

    initial clk = 0;
    always #5 clk = ~clk;

    integer i;
    reg [19:0] stim = 20'b00110100110001010110_0; // reversed so LSB = cycle 0... use array instead
    // stimulus sequence (matches stimulus.txt, cycle 0 first):
    reg [0:19] seq = {1'b0,1'b0,1'b1,1'b1,1'b0,1'b1,1'b0,1'b0,
                      1'b1,1'b1,1'b1,1'b0,1'b0,1'b1,1'b0,1'b1,
                      1'b1,1'b0,1'b0,1'b0};

    initial begin
        rst_n = 0; in = 0;
        @(posedge clk); @(posedge clk);
        rst_n = 1;
        for (i = 0; i < 20; i = i + 1) begin
            in = seq[i];
            @(posedge clk);
            #1;
            $display("cycle=%0d in=%b rise=%b", i, in, rise);
        end
        $finish;
    end
endmodule
