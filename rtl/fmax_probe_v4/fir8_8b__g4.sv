module fir8_8b__g4 (
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
    reg  [23:0] product0;
    reg  [23:0] product1;
    reg  [23:0] product2;
    reg  [23:0] product3;
    reg  [23:0] product4;
    reg  [23:0] product5;
    reg  [23:0] product6;
    reg  [23:0] product7;
    reg  [23:0] sum;
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
            product0 <= 24'd0;
            product1 <= 24'd0;
            product2 <= 24'd0;
            product3 <= 24'd0;
            product4 <= 24'd0;
            product5 <= 24'd0;
            product6 <= 24'd0;
            product7 <= 24'd0;
            sum <= 24'd0;
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
            product0 <= 8'd3 * delay0;
            product1 <= 8'd5 * delay1;
            product2 <= 8'd7 * delay2;
            product3 <= 8'd9 * delay3;
            product4 <= 8'd9 * delay4;
            product5 <= 8'd7 * delay5;
            product6 <= 8'd5 * delay6;
            product7 <= 8'd3 * delay7;
            sum <= product0 + product1 + product2 + product3 + product4 + product5 + product6 + product7;
            y <= sum[15:0];
        end
    end
endmodule