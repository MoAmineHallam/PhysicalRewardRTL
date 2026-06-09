// 10-bit add with carry/borrow out (registered).
module add10b (
    input  wire clk,
    input  wire rst_n,
    input  wire [9:0] a,
    input  wire [9:0] b,
    output reg  [10:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 11'd0;
        else result <= {1'b0, a} + {1'b0, b};
    end
endmodule
