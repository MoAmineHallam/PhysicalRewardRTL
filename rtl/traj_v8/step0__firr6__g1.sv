module step0__firr6__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  d1, d2, d3, d4, d5, d6;
    wire [23:0] acc = 8'd1 * d1 + 8'd2 * d2 + 8'd3 * d3 + 8'd4 * d4 + 8'd5 * d5 + 8'd6 * d6;
    always @(posedge clk) begin
        if (!rst_n) begin
            d1 <= 8'd0; d2 <= 8'd0; d3 <= 8'd0; d4 <= 8'd0; d5 <= 8'd0; d6 <= 8'd0; y <= 16'd0;
        end else begin
            d1 <= x;
            d2 <= d1;
            d3 <= d2;
            d4 <= d3;
            d5 <= d4;
            d6 <= d5;
            y <= acc[15:0];
        end
    end
endmodule