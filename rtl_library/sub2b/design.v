// 2-bit sub with carry/borrow out (registered).
module sub2b (
    input  wire clk,
    input  wire rst_n,
    input  wire [1:0] a,
    input  wire [1:0] b,
    output reg  [2:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 3'd0;
        else result <= {1'b0, a} - {1'b0, b};
    end
endmodule
