module grpo__poly7_v4_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= (((((((((16'd20 * x + 16'd77) * x + 16'd15) * x + 16'd31) * x + 16'd25) * x + 16'd28) * x + 16'd45) * x + 16'd10)) & 16'hFFFF);
    end
endmodule