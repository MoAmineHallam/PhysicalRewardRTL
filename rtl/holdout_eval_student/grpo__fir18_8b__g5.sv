module grpo__fir18_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [15:0] r0;
    reg [15:0] r1;
    reg [15:0] r2;
    reg [15:0] r3;
    reg [15:0] r4;
    reg [15:0] r5;
    reg [15:0] r6;
    reg [15:0] r7;
    reg [15:0] r8;
    reg [15:0] r9;
    reg [15:0] r10;
    reg [15:0] r11;
    reg [15:0] r12;
    reg [15:0] r13;
    reg [15:0] r14;
    reg [15:0] r15;
    reg [15:0] r16;
    reg [15:0] r17;
    always @(posedge clk) begin
        if (!rst_n) begin
            r0 <= 16'd0;
            r1 <= 16'd0;
            r2 <= 16'd0;
            r3 <= 16'd0;
            r4 <= 16'd0;
            r5 <= 16'd0;
            r6 <= 16'd0;
            r7 <= 16'd0;
            r8 <= 16'd0;
            r9 <= 16'd0;
            r10 <= 16'd0;
            r11 <= 16'd0;
            r12 <= 16'd0;
            r13 <= 16'd0;
            r14 <= 16'd0;
            r15 <= 16'd0;
            r16 <= 16'd0;
            r17 <= 16'd0;
        end else begin
            r0 <= 16'd3 * x + r1;
            r1 <= 16'd5 * x + r2;
            r2 <= 16'd7 * x + r3;
            r3 <= 16'd9 * x + r4;
            r4 <= 16'd11 * x + r5;
            r5 <= 16'd13 * x + r6;
            r6 <= 16'd15 * x + r7;
            r7 <= 16'd17 * x + r8;
            r8 <= 16'd19 * x + r9;
            r9 <= 16'd19 * x + r10;
            r10 <= 16'd17 * x + r11;
            r11 <= 16'd15 * x + r12;
            r12 <= 16'd13 * x + r13;
            r13 <= 16'd11 * x + r14;
            r14 <= 16'd9 * x + r15;
            r15 <= 16'd7 * x + r16;
            r16 <= 16'd5 * x + r17;
            r17 <= 16'd3 * x;
        end
    end
    always @(posedge clk) y <= r0[15:0];
endmodule