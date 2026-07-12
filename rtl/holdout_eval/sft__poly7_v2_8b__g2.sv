module sft__poly7_v2_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire [15:0] stage0 = 'd72;
    wire [15:0] stage1 = stage0 * x + 'd67;
    wire [15:0] stage2 = stage1 * x + 'd4;
    wire [15:0] stage3 = stage2 * x + 'd10;
    wire [15:0] stage4 = stage3 * x + 'd88;
    wire [15:0] stage5 = stage4 * x + 'd75;
    wire [15:0] stage6 = stage5 * x + 'd86;
    wire [15:0] stage7 = stage6 * x + 'd39;
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= stage7;
    end
endmodule