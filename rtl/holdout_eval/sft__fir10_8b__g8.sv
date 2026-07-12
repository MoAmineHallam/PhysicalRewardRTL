module sft__fir10_8b__g8 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  d0, d1, d2, d3, d4, d5, d6, d7, d8, d9;
    reg  [15:0] m0, m1, m2, m3, m4, m5, m6, m7, m8, m9, sum;
    always @(posedge clk) begin
        if (!rst_n) begin
            d0 <= 8'd0; d1 <= 8'd0; d2 <= 8'd0; d3 <= 8'd0; d4 <= 8'd0;
            d5 <= 8'd0; d6 <= 8'd0; d7 <= 8'd0; d8 <= 8'd0; d9 <= 8'd0;
            m0 <= 16'd0; m1 <= 16'd0; m2 <= 16'd0; m3 <= 16'd0; m4 <= 16'd0;
            m5 <= 16'd0; m6 <= 16'd0; m7 <= 16'd0; m8 <= 16'd0; m9 <= 16'd0;
            sum <= 16'd0; y <= 16'd0;
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
            m0 <= 8'd3 * d0;
            m1 <= 8'd5 * d1;
            m2 <= 8'd7 * d2;
            m3 <= 8'd9 * d3;
            m4 <= 8'd11 * d4;
            m5 <= 8'd11 * d5;
            m6 <= 8'd9 * d6;
            m7 <= 8'd7 * d7;
            m8 <= 8'd5 * d8;
            m9 <= 8'd3 * d9;
            sum <= m0 + m1 + m2 + m3 + m4 + m5 + m6 + m7 + m8 + m9;
            y <= sum;
        end
    end
endmodule