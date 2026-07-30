module sft__poly4_v7_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire [15:0] stage0 = 16'd24;
    wire [15:0] stage1 = stage0 * x + 16'd36;
    wire [15:0] stage2 = stage1 * x + 16'd17;
    wire [15:0] stage3 = stage2 * x + 16'd21;
    wire [15:0] stage4 = stage3 * x + 16'd50;
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= stage4;
    end
endmodule