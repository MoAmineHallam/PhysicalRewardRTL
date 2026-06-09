// 14-bit binary up-counter.
module counter14b (
    input  wire clk,
    input  wire rst_n,
    output reg  [13:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 14'd0;
        else        count <= count + 14'd1;
    end
endmodule
