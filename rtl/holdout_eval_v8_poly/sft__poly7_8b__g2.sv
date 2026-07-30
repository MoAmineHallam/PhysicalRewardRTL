module sft__poly7_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire [15:0] s0 = 1;
    wire [15:0] s1 = s0 * x + 3;
    wire [15:0] s2 = s1 * x + 5;
    wire [15:0] s3 = s2 * x + 7;
    wire [15:0] s4 = s3 * x + 9;
    wire [15:0] s5 = s4 * x + 11;
    wire [15:0] s6 = s5 * x + 13;
    wire [15:0] s7 = s6 * x + 15;
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= s7;
    end
endmodule