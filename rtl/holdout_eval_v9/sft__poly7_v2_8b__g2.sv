module sft__poly7_v2_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= (((((((((16'd72 * x + 16'd67) * x + 16'd4) * x + 16'd10) * x + 16'd88) * x + 16'd75) * x + 16'd86) * x + 16'd39)) & 16'hFFFF);
    end
endmodule