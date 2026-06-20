module fir8_8b__g9 (
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
    wire [23:0] acc = 8'd3 * delay0 + 8'd5 * delay1 + 8'd7 * delay2 + 8'd9 * delay3 + 8'd9 * delay4 + 8'd7 * delay5 + 8'd5 * delay6 + 8'd3 * delay7;
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
            y <= acc[15:0];
        end
    end
endmodule