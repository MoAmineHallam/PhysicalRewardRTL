module sft__poly7_v1_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= ((((((((16*x + 91) * x + 42) * x + 85) * x + 48) * x + 89) * x + 88) * x + 18)) & 16'hFFFF;
    end
endmodule