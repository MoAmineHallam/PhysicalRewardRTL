module sft__poly8_v9_8b__g1 (
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
    reg [7:0] xd1;
    reg [7:0] xd2;
    reg [7:0] xd3;
    reg [7:0] xd4;
    reg [7:0] xd5;
    reg [7:0] xd6;
    reg [7:0] xd7;
    reg [7:0] xd8;
    always @(posedge clk) begin
        if (!rst_n) begin r0 <= 16'd0; r1 <= 16'd0; r2 <= 16'd0; r3 <= 16'd0; r4 <= 16'd0; r5 <= 16'd0; r6 <= 16'd0; r7 <= 16'd0; r8 <= 16'd0; xd1 <= 8'd0; xd2 <= 8'd0; xd3 <= 8'd0; xd4 <= 8'd0; xd5 <= 8'd0; xd6 <= 8'd0; xd7 <= 8'd0; xd8 <= 8'd0; y <= 16'd0; end
        else begin
            r0 <= 16'd65;
            xd1 <= x;
            r1 <= r0 * xd1 + 16'd30;
            xd2 <= xd1;
            r2 <= r1 * xd2 + 16'd3;
            xd3 <= xd2;
            r3 <= r2 * xd3 + 16'd97;
            xd4 <= xd3;
            r4 <= r3 * xd4 + 16'd7;
            xd5 <= xd4;
            r5 <= r4 * xd5 + 16'd99;
            xd6 <= xd5;
            r6 <= r5 * xd6 + 16'd95;
            xd7 <= xd6;
            r7 <= r6 * xd7 + 16'd42;
            xd8 <= xd7;
            r8 <= r7 * xd8 + 16'd1;
            y <= r8;
        end
    end
endmodule
