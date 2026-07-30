module grpo__fir18_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 24'd0;
            a1 <= 24'd0;
            a2 <= 24'd0;
            a3 <= 24'd0;
            a4 <= 24'd0;
            a5 <= 24'd0;
            a6 <= 24'd0;
            a7 <= 24'd0;
            a8 <= 24'd0;
            a9 <= 24'd0;
            a10 <= 24'd0;
            a11 <= 24'd0;
            a12 <= 24'd0;
            a13 <= 24'd0;
            a14 <= 24'd0;
            a15 <= 24'd0;
            a16 <= 24'd0;
            a17 <= 24'd0;
            y <= 16'd0;
        end else begin
            a0 <= ((24'd3 * x) + a1) & 24'hFFFFF;
            a1 <= ((24'd5 * x) + a2) & 24'hFFFFF;
            a2 <= ((24'd7 * x) + a3) & 24'hFFFFF;
            a3 <= ((24'd9 * x) + a4) & 24'hFFFFF;
            a4 <= ((24'd11 * x) + a5) & 24'hFFFFF;
            a5 <= ((24'd13 * x) + a6) & 24'hFFFFF;
            a6 <= ((24'd15 * x) + a7) & 24'hFFFFF;
            a7 <= ((24'd17 * x) + a8) & 24'hFFFFF;
            a8 <= ((24'd19 * x) + a9) & 24'hFFFFF;
            a9 <= ((24'd19 * x) + a10) & 24'hFFFFF;
            a10 <= ((24'd17 * x) + a11) & 24'hFFFFF;
            a11 <= ((24'd15 * x) + a12) & 24'hFFFFF;
            a12 <= ((24'd13 * x) + a13) & 24'hFFFFF;
            a13 <= ((24'd11 * x) + a14) & 24'hFFFFF;
            a14 <= ((24'd9 * x) + a15) & 24'hFFFFF;
            a15 <= ((24'd7 * x) + a16) & 24'hFFFFF;
            a16 <= ((24'd5 * x) + a17) & 24'hFFFFF;
            a17 <= (24'd3 * x) & 24'hFFFFF;
            y <= a0[15:0];
        end
    end
endmodule