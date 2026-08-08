module sft__poly7_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire [15:0] t0 = 1;
    wire [15:0] t1 = t0 * x + 3;
    wire [15:0] t2 = t1 * x + 5;
    wire [15:0] t3 = t2 * x + 7;
    wire [15:0] t4 = t3 * x + 9;
    wire [15:0] t5 = t4 * x + 11;
    wire [15:0] t6 = t5 * x + 13;
    wire [15:0] t7 = t6 * x + 15;
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= t7;
    end
endmodule