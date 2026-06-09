// 16-bit magnitude comparator (registered): gt, eq, lt.
module cmp16b (
    input  wire clk,
    input  wire rst_n,
    input  wire [15:0] a,
    input  wire [15:0] b,
    output reg  gt, eq, lt
);
    always @(posedge clk) begin
        if (!rst_n) begin gt<=0; eq<=0; lt<=0; end
        else begin
            gt <= (a > b);
            eq <= (a == b);
            lt <= (a < b);
        end
    end
endmodule
