// 15-bit binary up-counter.
module counter15b (
    input  wire clk,
    input  wire rst_n,
    output reg  [14:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 15'd0;
        else        count <= count + 15'd1;
    end
endmodule
