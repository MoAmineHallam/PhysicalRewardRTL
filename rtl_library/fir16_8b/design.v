// 16-tap direct-form FIR filter, 8-bit unsigned samples, fixed 8-bit symmetric
// coefficients, single registered output (NOT pipelined).  The whole
// multiply-accumulate cone (16 products + adder tree) sits between the delay-
// line registers and the output register, so the register-to-register critical
// path is deliberately long -- this is the design under test for the silicon
// Fmax feasibility spike (expected ~100-200 MHz on xc7z020-1; if Vivado/silicon
// reports >250 MHz, bump to 32 taps / 12-bit data).
module fir16_8b (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:15];     // tapped delay line
    integer     i;
    reg  [20:0] acc;           // sum of 16 products, headroom to 17 bits used

    // combinational MAC cone (the long path feeding the output register)
    always @(*) begin
        acc = 8'd3  * xs[0]  + 8'd7  * xs[1]  + 8'd12 * xs[2]  + 8'd19 * xs[3]
            + 8'd27 * xs[4]  + 8'd34 * xs[5]  + 8'd40 * xs[6]  + 8'd43 * xs[7]
            + 8'd43 * xs[8]  + 8'd40 * xs[9]  + 8'd34 * xs[10] + 8'd27 * xs[11]
            + 8'd19 * xs[12] + 8'd12 * xs[13] + 8'd7  * xs[14] + 8'd3  * xs[15];
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 16; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 16; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule
