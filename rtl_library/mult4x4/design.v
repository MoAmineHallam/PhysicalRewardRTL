// Golden reference: registered 4x4 unsigned multiplier.
// Inputs: a=cnt[3:0], b=cnt[7:4]  -> product[7:0]  (period 256, divides 1024)
module mult4x4 (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [3:0] a,
    input  wire [3:0] b,
    output reg  [7:0] product
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) product <= 8'b0;
        else        product <= a * b;
    end
endmodule
