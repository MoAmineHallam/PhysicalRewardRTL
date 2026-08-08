module grpo__poly7_v3_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= (((((((((16'd85 * x + 16'd16) * x + 16'd89) * x + 16'd64) * x + 16'd12) * x + 16'd36) * x + 16'd50) * x + 16'd90)) & 16'hFFFF);
    end
endmodule