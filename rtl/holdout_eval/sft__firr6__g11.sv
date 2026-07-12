module sft__firr6__g11 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  d0, d1, d2, d3, d4, d5;
    wire [15:0] p0, p1, p2, p3, p4, p5;
    assign p0 = 8'd1 * d0;
    assign p1 = 8'd2 * d1;
    assign p2 = 8'd3 * d2;
    assign p3 = 8'd4 * d3;
    assign p4 = 8'd5 * d4;
    assign p5 = 8'd6 * d5;
    assign y = p0 + p1 + p2 + p3 + p4 + p5;
    always @(posedge clk) begin
        if (!rst_n) begin
            d0 <= 8'd0; d1 <= 8'd0; d2 <= 8'd0; d3 <= 8'd0; d4 <= 8'd0; d5 <= 8'd0;
        end else begin
            d0 <= x;
            d1 <= d0;
            d2 <= d1;
            d3 <= d2;
            d4 <= d3;
            d5 <= d4;
        end
    end
endmodule