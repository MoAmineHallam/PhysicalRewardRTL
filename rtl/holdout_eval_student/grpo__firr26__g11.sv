module grpo__firr26__g11 (
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
            y <= 16'd0;
        end else begin
            a0 <= 24'd1 * x + a1;
            a1 <= 24'd2 * x + a2;
            a2 <= 24'd3 * x + a3;
            a3 <= 24'd4 * x + a4;
            a4 <= 24'd5 * x + a5;
            a5 <= 24'd6 * x + a6;
            a6 <= 24'd7 * x + a7;
            a7 <= 24'd8 * x + a8;
            a8 <= 24'd9 * x + a9;
            a9 <= 24'd10 * x + a10;
            a10 <= 24'd11 * x + a11;
            a11 <= 24'd12 * x + a12;
            a12 <= 24'd13 * x + a13;
            a13 <= 24'd14 * x + a14;
            a14 <= 24'd15 * x + a15;
            a15 <= 24'd16 * x + a16;
            a16 <= 24'd17 * x + a17;
            a17 <= 24'd18 * x + a18;
            a18 <= 24'd19 * x + a19;
            a19 <= 24'd20 * x + a20;
            a20 <= 24'd21 * x + a21;
            a21 <= 24'd22 * x + a22;
            a22 <= 24'd23 * x + a23;
            a23 <= 24'd24 * x + a24;
            a24 <= 24'd25 * x + a25;
            a25 <= 24'd26 * x;
            y <= a0[15:0];
        end
    end
endmodule