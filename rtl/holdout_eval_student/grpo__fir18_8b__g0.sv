module grpo__fir18_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] d0, d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, d15, d16, d17;
    always @(posedge clk) begin
        if (!rst_n) begin
            d0 <= 24'd0;
            d1 <= 24'd0;
            d2 <= 24'd0;
            d3 <= 24'd0;
            d4 <= 24'd0;
            d5 <= 24'd0;
            d6 <= 24'd0;
            d7 <= 24'd0;
            d8 <= 24'd0;
            d9 <= 24'd0;
            d10 <= 24'd0;
            d11 <= 24'd0;
            d12 <= 24'd0;
            d13 <= 24'd0;
            d14 <= 24'd0;
            d15 <= 24'd0;
            d16 <= 24'd0;
            d17 <= 24'd0;
            y <= 16'd0;
        end else begin
            d0 <= 24'd3 * x + d1;
            d1 <= 24'd5 * x + d2;
            d2 <= 24'd7 * x + d3;
            d3 <= 24'd9 * x + d4;
            d4 <= 24'd11 * x + d5;
            d5 <= 24'd13 * x + d6;
            d6 <= 24'd15 * x + d7;
            d7 <= 24'd17 * x + d8;
            d8 <= 24'd19 * x + d9;
            d9 <= 24'd19 * x + d10;
            d10 <= 24'd17 * x + d11;
            d11 <= 24'd15 * x + d12;
            d12 <= 24'd13 * x + d13;
            d13 <= 24'd11 * x + d14;
            d14 <= 24'd9 * x + d15;
            d15 <= 24'd7 * x + d16;
            d16 <= 24'd5 * x + d17;
            d17 <= 24'd3 * x;
            y <= d0[15:0];
        end
    end
endmodule