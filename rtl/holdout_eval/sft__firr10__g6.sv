module sft__firr10__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0]  d0, d1, d2, d3, d4, d5, d6, d7, d8, d9;
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            d0 <= 8'd0; d1 <= 8'd0; d2 <= 8'd0; d3 <= 8'd0; d4 <= 8'd0;
            d5 <= 8'd0; d6 <= 8'd0; d7 <= 8'd0; d8 <= 8'd0; d9 <= 8'd0;
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
            i = 0;
            y <= (i+1)*d0 + (i+2)*d1 + (i+3)*d2 + (i+4)*d3 + (i+5)*d4 + (i+6)*d5 + (i+7)*d6 + (i+8)*d7 + (i+9)*d8 + (i+10)*d9;
        end
    end
endmodule