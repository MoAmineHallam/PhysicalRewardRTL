// 3-bit binary up-counter.
module counter3b (
    input  wire clk,
    input  wire rst_n,
    output reg  [2:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 3'd0;
        else        count <= count + 3'd1;
    end
endmodule
