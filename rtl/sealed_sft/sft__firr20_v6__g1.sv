module sft__firr20_v6__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] d0, d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, d15, d16, d17, d18, d19;
    wire [23:0] acc = 8'd4 * d0 +
                     8'd8 * d1 +
                     8'd12 * d2 +
                     8'd16 * d3 +
                     8'd20 * d4 +
                     8'd24 * d5 +
                     8'd28 * d6 +
                     8'd32 * d7 +
                     8'd36 * d8 +
                     8'd40 * d9 +
                     8'd44 * d10 +
                     8'd48 * d11 +
                     8'd52 * d12 +
                     8'd56 * d13 +
                     8'd60 * d14 +
                     8'd64 * d15 +
                     8'd68 * d16 +
                     8'd72 * d17 +
                     8'd76 * d18 +
                     8'd80 * d19;
    always @(posedge clk) begin
        if (!rst_n) begin
            d0 <= 8'd0; d1 <= 8'd0; d2 <= 8'd0; d3 <= 8'd0; d4 <= 8'd0; d5 <= 8'd0; d6 <= 8'd0; d7 <= 8'd0; d8 <= 8'd0; d9 <= 8'd0; d10 <= 8'd0; d11 <= 8'd0; d12 <= 8'd0; d13 <= 8'd0; d14 <= 8'd0; d15 <= 8'd0; d16 <= 8'd0; d17 <= 8'd0; d18 <= 8'd0; d19 <= 8'd0; y <= 16'd0;
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
            d13 <= d12;
            d14 <= d13;
            d15 <= d14;
            d16 <= d15;
            d17 <= d16;
            d18 <= d17;
            d19 <= d18;
            y <= acc[15:0];
        end
    end
endmodule
