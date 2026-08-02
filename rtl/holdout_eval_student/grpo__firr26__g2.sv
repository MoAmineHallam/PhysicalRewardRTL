module grpo__firr26__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0;
    reg [23:0] a1;
    reg [23:0] a2;
    reg [23:0] a3;
    reg [23:0] a4;
    reg [23:0] a5;
    reg [23:0] a6;
    reg [23:0] a7;
    reg [23:0] a8;
    reg [23:0] a9;
    reg [23:0] a10;
    reg [23:0] a11;
    reg [23:0] a12;
    reg [23:0] a13;
    reg [23:0] a14;
    reg [23:0] a15;
    reg [23:0] a16;
    reg [23:0] a17;
    reg [23:0] a18;
    reg [23:0] a19;
    reg [23:0] a20;
    reg [23:0] a21;
    reg [23:0] a22;
    reg [23:0] a23;
    reg [23:0] a24;
    reg [23:0] a25;
    reg [7:0] xd1;
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
            a18 <= 24'd0;
            a19 <= 24'd0;
            a20 <= 24'd0;
            a21 <= 24'd0;
            a22 <= 24'd0;
            a23 <= 24'd0;
            a24 <= 24'd0;
            a25 <= 24'd0;
            xd1 <= 8'd0;
        end else begin
            a0 <= 24'd1 * xd1 + a1;
            a1 <= 24'd2 * xd1 + a2;
            a2 <= 24'd3 * xd1 + a3;
            a3 <= 24'd4 * xd1 + a4;
            a4 <= 24'd5 * xd1 + a5;
            a5 <= 24'd6 * xd1 + a6;
            a6 <= 24'd7 * xd1 + a7;
            a7 <= 24'd8 * xd1 + a8;
            a8 <= 24'd9 * xd1 + a9;
            a9 <= 24'd10 * xd1 + a10;
            a10 <= 24'd11 * xd1 + a11;
            a11 <= 24'd12 * xd1 + a12;
            a12 <= 24'd13 * xd1 + a13;
            a13 <= 24'd14 * xd1 + a14;
            a14 <= 24'd15 * xd1 + a15;
            a15 <= 24'd16 * xd1 + a16;
            a16 <= 24'd17 * xd1 + a17;
            a17 <= 24'd18 * xd1 + a18;
            a18 <= 24'd19 * xd1 + a19;
            a19 <= 24'd20 * xd1 + a20;
            a20 <= 24'd21 * xd1 + a21;
            a21 <= 24'd22 * xd1 + a22;
            a22 <= 24'd23 * xd1 + a23;
            a23 <= 24'd24 * xd1 + a24;
            a24 <= 24'd25 * xd1 + a25;
            a25 <= 24'd26 * xd1;
            xd1 <= x;
            y <= a0[15:0];
        end
    end
endmodule