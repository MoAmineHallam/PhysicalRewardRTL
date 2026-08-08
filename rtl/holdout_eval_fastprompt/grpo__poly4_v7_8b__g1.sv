module grpo__poly4_v7_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire [15:0] t0 = 16'd24;
    wire [15:0] t1 = t0 * x + 16'd36;
    wire [15:0] t2 = t1 * x + 16'd17;
    wire [15:0] t3 = t2 * x + 16'd21;
    wire [15:0] t4 = t3 * x + 16'd50;
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= t4;
    end
endmodule