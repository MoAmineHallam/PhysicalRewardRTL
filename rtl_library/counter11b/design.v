// 11-bit binary up-counter.
module counter11b (
    input  wire clk,
    input  wire rst_n,
    output reg  [10:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 11'd0;
        else        count <= count + 11'd1;
    end
endmodule
