module grpo__fir6_8b__g10 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [8:0]  a0, a1, a2, a3, a4, a5;
    wire [15:0] y_reg = 9'd3 * a0 + 9'd5 * a1 + 9'd7 * a2 + 9'd7 * a3 + 9'd5 * a4 + 9'd3 * a5;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 9'd0; a1 <= 9'd0; a2 <= 9'd0; a3 <= 9'd0; a4 <= 9'd0; a5 <= 9'd0; y <= 16'd0;
        end else begin
            a0 <= x;
            a1 <= a0;
            a2 <= a1;
            a3 <= a2;
            a4 <= a3;
            a5 <= a4;
            y <= y_reg;
        end
    end
endmodule