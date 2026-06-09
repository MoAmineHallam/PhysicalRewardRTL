// 2-bit binary up-counter.
module counter2b (
    input  wire clk,
    input  wire rst_n,
    output reg  [1:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 2'd0;
        else        count <= count + 2'd1;
    end
endmodule
