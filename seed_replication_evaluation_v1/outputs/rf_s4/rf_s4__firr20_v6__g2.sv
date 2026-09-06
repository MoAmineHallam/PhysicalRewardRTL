module rf_s4__firr20_v6__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 24'd0; a1 <= 24'd0; a2 <= 24'd0; a3 <= 24'd0; a4 <= 24'd0; a5 <= 24'd0; a6 <= 24'd0; a7 <= 24'd0; a8 <= 24'd0; a9 <= 24'd0; a10 <= 24'd0; a11 <= 24'd0; a12 <= 24'd0; a13 <= 24'd0; a14 <= 24'd0; a15 <= 24'd0; a16 <= 24'd0; a17 <= 24'd0; a18 <= 24'd0; a19 <= 24'd0; y <= 16'd0;
        end else begin
            a0 <= 24'd4 * x + a1;
            a1 <= 24'd8 * x + a2;
            a2 <= 24'd12 * x + a3;
            a3 <= 24'd16 * x + a4;
            a4 <= 24'd20 * x + a5;
            a5 <= 24'd24 * x + a6;
            a6 <= 24'd28 * x + a7;
            a7 <= 24'd32 * x + a8;
            a8 <= 24'd36 * x + a9;
            a9 <= 24'd40 * x + a10;
            a10 <= 24'd44 * x + a11;
            a11 <= 24'd48 * x + a12;
            a12 <= 24'd52 * x + a13;
            a13 <= 24'd56 * x + a14;
            a14 <= 24'd60 * x + a15;
            a15 <= 24'd64 * x + a16;
            a16 <= 24'd68 * x + a17;
            a17 <= 24'd72 * x + a18;
            a18 <= 24'd76 * x + a19;
            a19 <= 24'd80 * x;
            y <= a0[15:0];
        end
    end
endmodule
