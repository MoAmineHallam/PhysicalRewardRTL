// 10-bit binary up-counter.
module counter10b (
    input  wire clk,
    input  wire rst_n,
    output reg  [9:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 10'd0;
        else        count <= count + 10'd1;
    end
endmodule
