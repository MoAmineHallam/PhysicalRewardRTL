// 7-bit binary up-counter.
module counter7b (
    input  wire clk,
    input  wire rst_n,
    output reg  [6:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 7'd0;
        else        count <= count + 7'd1;
    end
endmodule
