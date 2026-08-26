module sft__fir13_v6_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  d0, d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12;
    wire [23:0] acc = 8'd19 * d0 + 8'd28 * d1 + 8'd42 * d2 + 8'd41 * d3 + 8'd60 * d4 + 8'd8 * d5 + 8'd17 * d6 + 8'd9 * d7 + 8'd28 * d8 + 8'd42 * d9 + 8'd19 * d10 + 8'd44 * d11 + 8'd37 * d12;
    always @(posedge clk) begin
        if (!rst_n) begin
            d0 <= 8'd0; d1 <= 8'd0; d2 <= 8'd0; d3 <= 8'd0; d4 <= 8'd0; d5 <= 8'd0; d6 <= 8'd0; d7 <= 8'd0; d8 <= 8'd0; d9 <= 8'd0; d10 <= 8'd0; d11 <= 8'd0; d12 <= 8'd0; y <= 16'd0;
        end else begin
            d0 <= x;
            d1 <= d0;
            d2 <= d1;
            d3 <= d2;
            d4 <= d3;
            d5 <= d4;
            d6 <= d5;
            d7 <= d6;
            d8 <= d7;
            d9 <= d8;
            d10 <= d9;
            d11 <= d10;
            d12 <= d11;
            y <= acc[15:0];
        end
    end
endmodule
