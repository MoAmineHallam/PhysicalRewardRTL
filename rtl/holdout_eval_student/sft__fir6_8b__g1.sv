module sft__fir6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] accum;
    reg [7:0] d0, d1, d2, d3, d4, d5;
    always @(posedge clk) begin
        if (!rst_n) begin
            accum <= 24'd0;
            d0 <= 8'd0; d1 <= 8'd0; d2 <= 8'd0; d3 <= 8'd0; d4 <= 8'd0; d5 <= 8'd0;
        end else begin
            accum <= 24'd3 * d0 + 24'd5 * d1 + 24'd7 * d2 + 24'd7 * d3 + 24'd5 * d4 + 24'd3 * d5;
            d0 <= x; d1 <= d0; d2 <= d1; d3 <= d2; d4 <= d3; d5 <= d4;
            y <= accum[15:0];
        end
    end
endmodule