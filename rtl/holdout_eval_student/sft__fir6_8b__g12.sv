module sft__fir6_8b__g12 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] d0;
    reg [23:0] d1;
    reg [23:0] d2;
    reg [23:0] d3;
    reg [23:0] d4;
    reg [23:0] d5;
    always @(posedge clk) begin
        if (!rst_n) begin
            d0 <= 24'd0;
            d1 <= 24'd0;
            d2 <= 24'd0;
            d3 <= 24'd0;
            d4 <= 24'd0;
            d5 <= 24'd0;
            y <= 16'd0;
        end else begin
            d0 <= 8'd3 * x + d1;
            d1 <= 8'd5 * x + d2;
            d2 <= 8'd7 * x + d3;
            d3 <= 8'd7 * x + d4;
            d4 <= 8'd5 * x + d5;
            d5 <= 8'd3 * x;
            y <= d0[15:0];
        end
    end
endmodule