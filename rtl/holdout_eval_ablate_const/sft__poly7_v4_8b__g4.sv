module sft__poly7_v4_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire [15:0] t0 =       20;
    wire [15:0] t1 = t0 * x + 77;
    wire [15:0] t2 = t1 * x + 15;
    wire [15:0] t3 = t2 * x + 31;
    wire [15:0] t4 = t3 * x + 25;
    wire [15:0] t5 = t4 * x + 28;
    wire [15:0] t6 = t5 * x + 45;
    wire [15:0] t7 = t6 * x + 10;
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= t7;
    end
endmodule