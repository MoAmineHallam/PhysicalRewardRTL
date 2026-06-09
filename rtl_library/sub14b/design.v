// 14-bit sub with carry/borrow out (registered).
module sub14b (
    input  wire clk,
    input  wire rst_n,
    input  wire [13:0] a,
    input  wire [13:0] b,
    output reg  [14:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 15'd0;
        else result <= {1'b0, a} - {1'b0, b};
    end
endmodule
