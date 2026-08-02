module sft__fir6_8b__g15 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] w0, w1, w2, w3, w4, w5;
    always @(posedge clk) begin
        if (!rst_n) begin
            w0 <= 24'd0;
            w1 <= 24'd0;
            w2 <= 24'd0;
            w3 <= 24'd0;
            w4 <= 24'd0;
            w5 <= 24'd0;
            y <= 16'd0;
        end else begin
            w0 <= 24'd3 * x + w1;
            w1 <= 24'd5 * x + w2;
            w2 <= 24'd7 * x + w3;
            w3 <= 24'd7 * x + w4;
            w4 <= 24'd5 * x + w5;
            w5 <= 24'd3 * x;
            y <= w0[15:0];
        end
    end
endmodule