// 4-bit sub with carry/borrow out (registered).
module sub4b (
    input  wire clk,
    input  wire rst_n,
    input  wire [3:0] a,
    input  wire [3:0] b,
    output reg  [4:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 5'd0;
        else result <= {1'b0, a} - {1'b0, b};
    end
endmodule
