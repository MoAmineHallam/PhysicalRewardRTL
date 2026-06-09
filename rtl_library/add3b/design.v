// 3-bit add with carry/borrow out (registered).
module add3b (
    input  wire clk,
    input  wire rst_n,
    input  wire [2:0] a,
    input  wire [2:0] b,
    output reg  [3:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 4'd0;
        else result <= {1'b0, a} + {1'b0, b};
    end
endmodule
