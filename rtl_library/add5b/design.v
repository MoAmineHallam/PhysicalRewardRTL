// 5-bit add with carry/borrow out (registered).
module add5b (
    input  wire clk,
    input  wire rst_n,
    input  wire [4:0] a,
    input  wire [4:0] b,
    output reg  [5:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 6'd0;
        else result <= {1'b0, a} + {1'b0, b};
    end
endmodule
