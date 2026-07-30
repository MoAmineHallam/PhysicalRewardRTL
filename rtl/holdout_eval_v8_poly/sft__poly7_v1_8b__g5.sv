module sft__poly7_v1_8b__g5 (
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
        if (!rst_n) begin r0 <= 16; r1 <= 0; r2 <= 0; r3 <= 0; r4 <= 0; r5 <= 0; r6 <= 0; r7 <= 0; xd1 <= 8'd0; xd2 <= 8'd0; xd3 <= 8'd0; xd4 <= 8'd0; xd5 <= 8'd0; xd6 <= 8'd0; xd7 <= 8'd0; y <= 16; end
        else begin
            r0 <= 16;
            xd1 <= x;
            r1 <= r0 * xd1 + 91;
            xd2 <= xd1;
            r2 <= r1 * xd2 + 42;
            xd3 <= xd2;
            r3 <= r2 * xd3 + 85;
            xd4 <= xd3;
            r4 <= r3 * xd4 + 48;
            xd5 <= xd4;
            r5 <= r4 * xd5 + 89;
            xd6 <= xd5;
            r6 <= r5 * xd6 + 88;
            xd7 <= xd6;
            r7 <= r6 * xd7 + 18;
            y <= r7;
        end
    end
endmodule