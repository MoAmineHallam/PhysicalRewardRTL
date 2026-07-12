module sft__fir6_8b__g9 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  d0, d1, d2, d3, d4, d5;
    wire [15:0] t0, t1, t2, t3, t4, t5, t6;
    assign t0 = 8'd3 * d0;
    assign t1 = 8'd5 * d1;
    assign t2 = 8'd7 * d2;
    assign t3 = 8'd7 * d3;
    assign t4 = 8'd5 * d4;
    assign t5 = 8'd3 * d5;
    assign t6 = t0 + t1 + t2 + t3 + t4 + t5;
    always @(posedge clk) begin
        if (!rst_n) begin
            d0 <= 8'd0; d1 <= 8'd0; d2 <= 8'd0; d3 <= 8'd0; d4 <= 8'd0; d5 <= 8'd0; y <= 16'd0;
        end else begin
            d0 <= x;
            d1 <= d0;
            d2 <= d1;
            d3 <= d2;
            d4 <= d3;
            d5 <= d4;
            y <= t6;
        end
    end
endmodule