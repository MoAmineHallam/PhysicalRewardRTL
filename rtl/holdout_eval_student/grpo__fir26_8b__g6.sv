module grpo__fir26_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] d0, d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, d15, d16, d17, d18, d19, d20, d21, d22, d23, d24, d25;
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
            d18 <= 24'd0;
            d19 <= 24'd0;
            d20 <= 24'd0;
            d21 <= 24'd0;
            d22 <= 24'd0;
            d23 <= 24'd0;
            d24 <= 24'd0;
            d25 <= 24'd0;
            y <= 16'd0;
        end else begin
            d0 <= (8'd3 * x) + d1;
            d1 <= (8'd5 * x) + d2;
            d2 <= (8'd7 * x) + d3;
            d3 <= (8'd9 * x) + d4;
            d4 <= (8'd11 * x) + d5;
            d5 <= (8'd13 * x) + d6;
            d6 <= (8'd15 * x) + d7;
            d7 <= (8'd17 * x) + d8;
            d8 <= (8'd19 * x) + d9;
            d9 <= (8'd21 * x) + d10;
            d10 <= (8'd23 * x) + d11;
            d11 <= (8'd25 * x) + d12;
            d12 <= (8'd27 * x) + d13;
            d13 <= (8'd27 * x) + d14;
            d14 <= (8'd25 * x) + d15;
            d15 <= (8'd23 * x) + d16;
            d16 <= (8'd21 * x) + d17;
            d17 <= (8'd19 * x) + d18;
            d18 <= (8'd17 * x) + d19;
            d19 <= (8'd15 * x) + d20;
            d20 <= (8'd13 * x) + d21;
            d21 <= (8'd11 * x) + d22;
            d22 <= (8'd9 * x) + d23;
            d23 <= (8'd7 * x) + d24;
            d24 <= (8'd5 * x) + d25;
            d25 <= (8'd3 * x);
            y <= d0[15:0];
        end
    end
endmodule