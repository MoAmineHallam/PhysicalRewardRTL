module sft__poly7_v3_8b__g6 (
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
    reg [7:0] xd1;
    reg [7:0] xd2;
    reg [7:0] xd3;
    reg [7:0] xd4;
    reg [7:0] xd5;
    reg [7:0] xd6;
    reg [7:0] xd7;
    always @(posedge clk) begin
        if (!rst_n) begin
            r0 <= 0;
            r1 <= 0;
            r2 <= 0;
            r3 <= 0;
            r4 <= 0;
            r5 <= 0;
            r6 <= 0;
            r7 <= 0;
            xd1 <= 0;
            xd2 <= 0;
            xd3 <= 0;
            xd4 <= 0;
            xd5 <= 0;
            xd6 <= 0;
            xd7 <= 0;
        end else begin
            r0 <= 85;
            xd1 <= x;
            r1 <= r0 * xd1 + 16;
            xd2 <= xd1;
            r2 <= r1 * xd2 + 89;
            xd3 <= xd2;
            r3 <= r2 * xd3 + 64;
            xd4 <= xd3;
            r4 <= r3 * xd4 + 12;
            xd5 <= xd4;
            r5 <= r4 * xd5 + 36;
            xd6 <= xd5;
            r6 <= r5 * xd6 + 50;
            xd7 <= xd6;
            r7 <= r6 * xd7 + 90;
            y <= r7;
        end
    end
endmodule