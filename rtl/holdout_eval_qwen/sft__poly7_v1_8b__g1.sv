module sft__poly7_v1_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire [15:0] t0 = 16'd16;
    wire [15:0] t1 = t0 * x + 16'd91;
    wire [15:0] t2 = t1 * x + 16'd42;
    wire [15:0] t3 = t2 * x + 16'd85;
    wire [15:0] t4 = t3 * x + 16'd48;
    wire [15:0] t5 = t4 * x + 16'd89;
    wire [15:0] t6 = t5 * x + 16'd88;
    wire [15:0] t7 = t6 * x + 16'd18;
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= t7;
    end
endmodule