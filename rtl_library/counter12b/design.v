// 12-bit binary up-counter.
module counter12b (
    input  wire clk,
    input  wire rst_n,
    output reg  [11:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 12'd0;
        else        count <= count + 12'd1;
    end
endmodule
