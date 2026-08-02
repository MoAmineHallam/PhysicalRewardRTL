module sft__fir10_8b__g13 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] w0;
    reg [23:0] w1;
    reg [23:0] w2;
    reg [23:0] w3;
    reg [23:0] w4;
    reg [23:0] w5;
    reg [23:0] w6;
    reg [23:0] w7;
    reg [23:0] w8;
    reg [23:0] w9;
    always @(posedge clk) begin
        if (!rst_n) begin
            w0 <= 24'd0;
            w1 <= 24'd0;
            w2 <= 24'd0;
            w3 <= 24'd0;
            w4 <= 24'd0;
            w5 <= 24'd0;
            w6 <= 24'd0;
            w7 <= 24'd0;
            w8 <= 24'd0;
            w9 <= 24'd0;
            y <= 16'd0;
        end else begin
            w0 <= 8'd3 * x + w1;
            w1 <= 8'd5 * x + w2;
            w2 <= 8'd7 * x + w3;
            w3 <= 8'd9 * x + w4;
            w4 <= 8'd11 * x + w5;
            w5 <= 8'd11 * x + w6;
            w6 <= 8'd9 * x + w7;
            w7 <= 8'd7 * x + w8;
            w8 <= 8'd5 * x + w9;
            w9 <= 8'd3 * x;
            y <= w0[15:0];
        end
    end
endmodule