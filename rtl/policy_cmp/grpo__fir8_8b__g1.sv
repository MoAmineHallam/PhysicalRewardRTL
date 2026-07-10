module grpo__fir8_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [23:0] d0, d1, d2, d3, d4, d5, d6, d7;
    always @(posedge clk) begin
        if (!rst_n) begin
            d0 <= 24'd0; d1 <= 24'd0; d2 <= 24'd0; d3 <= 24'd0; d4 <= 24'd0; d5 <= 24'd0; d6 <= 24'd0; d7 <= 24'd0; y <= 16'd0;
        end else begin
            d0 <= 8'd3 * x + d1;
            d1 <= 8'd5 * x + d2;
            d2 <= 8'd7 * x + d3;
            d3 <= 8'd9 * x + d4;
            d4 <= 8'd9 * x + d5;
            d5 <= 8'd7 * x + d6;
            d6 <= 8'd5 * x + d7;
            d7 <= 8'd3 * x;
            y <= d0[15:0];
        end
    end
endmodule