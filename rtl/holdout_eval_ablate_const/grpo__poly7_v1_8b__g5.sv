module grpo__poly7_v1_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= (((((((((16'd16 * x + 16'd91) * x + 16'd42) * x + 16'd85) * x + 16'd48) * x + 16'd89) * x + 16'd88) * x + 16'd18)) & 16'hFFFF);
    end
endmodule