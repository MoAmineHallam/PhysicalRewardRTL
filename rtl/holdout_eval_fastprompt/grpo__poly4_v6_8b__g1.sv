module grpo__poly4_v6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= (((((16'd65 * x + 16'd29) * x + 16'd88) * x + 16'd44) * x + 16'd17)) & 16'hFFFF;
    end
endmodule