module mlp_s2__poly12_v15_8b__g4 (
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
    reg [7:0] xd1;
    reg [7:0] xd2;
    reg [7:0] xd3;
    reg [7:0] xd4;
    reg [7:0] xd5;
    reg [7:0] xd6;
    reg [7:0] xd7;
    reg [7:0] xd8;
    reg [7:0] xd9;
    reg [7:0] xd10;
    reg [7:0] xd11;
    reg [7:0] xd12;
    reg [7:0] xd13;
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
            xd1 <= 8'd0;
            xd2 <= 8'd0;
            xd3 <= 8'd0;
            xd4 <= 8'd0;
            xd5 <= 8'd0;
            xd6 <= 8'd0;
            xd7 <= 8'd0;
            xd8 <= 8'd0;
            xd9 <= 8'd0;
            xd10 <= 8'd0;
            xd11 <= 8'd0;
            xd12 <= 8'd0;
            xd13 <= 8'd0;
        end else begin
            r0 <= 16'd48;
            xd1 <= x;
            r1 <= r0 * xd1 + 16'd24;
            xd2 <= xd1;
            r2 <= r1 * xd2 + 16'd79;
            xd3 <= xd2;
            r3 <= r2 * xd3 + 16'd2;
            xd4 <= xd3;
            r4 <= r3 * xd4 + 16'd46;
            xd5 <= xd4;
            r5 <= r4 * xd5 + 16'd35;
            xd6 <= xd5;
            r6 <= r5 * xd6 + 16'd44;
            xd7 <= xd6;
            r7 <= r6 * xd7 + 16'd66;
            xd8 <= xd7;
            r8 <= r7 * xd8 + 16'd80;
            xd9 <= xd8;
            r9 <= r8 * xd9 + 16'd64;
            xd10 <= xd9;
            r10 <= r9 * xd10 + 16'd18;
            xd11 <= xd10;
            r11 <= r10 * xd11 + 16'd58;
            xd12 <= xd11;
            r12 <= r11 * xd12 + 16'd51;
        end
    end
    always @(posedge clk) begin
        y <= r12;
    end
endmodule
