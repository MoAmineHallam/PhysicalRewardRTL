module fir4_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  delay0, delay1, delay2, delay3;
    wire [23:0] acc = 8'd3 * delay0 + 8'd5 * delay1 + 8'd5 * delay2 + 8'd3 * delay3;
    always @(posedge clk) begin
        if (!rst_n) begin
            delay0 <= 8'd0; delay1 <= 8'd0; delay2 <= 8'd0; delay3 <= 8'd0; y <= 16'd0;
        end else begin
            delay0 <= x;
            delay1 <= delay0;
            delay2 <= delay1;
            delay3 <= delay2;
            y <= acc[15:0];
        end
    end
endmodule