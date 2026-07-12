module sft__firr10__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  d0;
    reg  [7:0]  d1;
    reg  [7:0]  d2;
    reg  [7:0]  d3;
    reg  [7:0]  d4;
    reg  [7:0]  d5;
    reg  [7:0]  d6;
    reg  [7:0]  d7;
    reg  [7:0]  d8;
    reg  [7:0]  d9;
    always @(posedge clk) begin
        if (!rst_n) begin
            d0 <= 8'd0;
            d1 <= 8'd0;
            d2 <= 8'd0;
            d3 <= 8'd0;
            d4 <= 8'd0;
            d5 <= 8'd0;
            d6 <= 8'd0;
            d7 <= 8'd0;
            d8 <= 8'd0;
            d9 <= 8'd0;
            y <= 16'd0;
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
            y <= 8'd1 * d0 + 8'd2 * d1 + 8'd3 * d2 + 8'd4 * d3 + 8'd5 * d4 + 8'd6 * d5 + 8'd7 * d6 + 8'd8 * d7 + 8'd9 * d8 + 8'd10 * d9;
        end
    end
endmodule