module fir8_8b__g7 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  delay0;
    reg  [7:0]  delay1;
    reg  [7:0]  delay2;
    reg  [7:0]  delay3;
    reg  [7:0]  delay4;
    reg  [7:0]  delay5;
    reg  [7:0]  delay6;
    reg  [7:0]  delay7;
    wire [7:0]  product0 = 8'd3;
    wire [7:0]  product1 = 8'd5;
    wire [7:0]  product2 = 8'd7;
    wire [7:0]  product3 = 8'd9;
    wire [7:0]  product4 = 8'd9;
    wire [7:0]  product5 = 8'd7;
    wire [7:0]  product6 = 8'd5;
    wire [7:0]  product7 = 8'd3;
    wire [15:0] sum = product0 * delay0 + product1 * delay1 + product2 * delay2 + product3 * delay3 + product4 * delay4 + product5 * delay5 + product6 * delay6 + product7 * delay7;
    always @(posedge clk) begin
        if (!rst_n) begin
            delay0 <= 8'd0;
            delay1 <= 8'd0;
            delay2 <= 8'd0;
            delay3 <= 8'd0;
            delay4 <= 8'd0;
            delay5 <= 8'd0;
            delay6 <= 8'd0;
            delay7 <= 8'd0;
            y <= 16'd0;
        end else begin
            delay0 <= x;
            delay1 <= delay0;
            delay2 <= delay1;
            delay3 <= delay2;
            delay4 <= delay3;
            delay5 <= delay4;
            delay6 <= delay5;
            delay7 <= delay6;
            y <= sum;
        end
    end
endmodule