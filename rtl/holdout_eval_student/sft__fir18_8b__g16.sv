module sft__fir18_8b__g16 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
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
    reg [15:0] r18;
    wire [31:0] w1 = 3 * x + r2;
    wire [31:0] w2 = 5 * x + r3;
    wire [31:0] w3 = 7 * x + r4;
    wire [31:0] w4 = 9 * x + r5;
    wire [31:0] w5 = 11 * x + r6;
    wire [31:0] w6 = 13 * x + r7;
    wire [31:0] w7 = 15 * x + r8;
    wire [31:0] w8 = 17 * x + r9;
    wire [31:0] w9 = 19 * x + r10;
    wire [31:0] w10 = 19 * x + r11;
    wire [31:0] w11 = 17 * x + r12;
    wire [31:0] w12 = 15 * x + r13;
    wire [31:0] w13 = 13 * x + r14;
    wire [31:0] w14 = 11 * x + r15;
    wire [31:0] w15 = 9 * x + r16;
    wire [31:0] w16 = 7 * x + r17;
    wire [31:0] w17 = 5 * x + r18;
    wire [31:0] w18 = 3 * x;
    always @(posedge clk) begin
        if (!rst_n) begin
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
            r18 <= 16'd0;
            y <= 16'd0;
        end else begin
            r1 <= w1;
            r2 <= w2;
            r3 <= w3;
            r4 <= w4;
            r5 <= w5;
            r6 <= w6;
            r7 <= w7;
            r8 <= w8;
            r9 <= w9;
            r10 <= w10;
            r11 <= w11;
            r12 <= w12;
            r13 <= w13;
            r14 <= w14;
            r15 <= w15;
            r16 <= w16;
            r17 <= w17;
            r18 <= w18;
            y <= r1[15:0];
        end
    end
endmodule