module grpo__fir6_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a1, a2, a3, a4, a5, a6;
    always @(posedge clk) begin
        if (!rst_n) begin
            a1 <= 24'd0;
            a2 <= 24'd0;
            a3 <= 24'd0;
            a4 <= 24'd0;
            a5 <= 24'd0;
            a6 <= 24'd0;
            y <= 16'd0;
        end else begin
            a1 <= (24'd3 * x) + a2;
            a2 <= (24'd5 * x) + a3;
            a3 <= (24'd7 * x) + a4;
            a4 <= (24'd7 * x) + a5;
            a5 <= (24'd5 * x) + a6;
            a6 <= (24'd3 * x);
            y <= a1[15:0];
        end
    end
endmodule