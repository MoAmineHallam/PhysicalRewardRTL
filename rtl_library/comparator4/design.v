// Golden reference: registered 4-bit magnitude comparator.
// Inputs: a=cnt[3:0], b=cnt[7:4]  -> {gt, eq, lt}  (period 256, divides 1024)
module comparator4 (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [3:0] a,
    input  wire [3:0] b,
    output reg        gt,   // a > b
    output reg        eq,   // a == b
    output reg        lt    // a < b
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            gt <= 1'b0; eq <= 1'b0; lt <= 1'b0;
        end else begin
            gt <= (a > b);
            eq <= (a == b);
            lt <= (a < b);
        end
    end
endmodule
