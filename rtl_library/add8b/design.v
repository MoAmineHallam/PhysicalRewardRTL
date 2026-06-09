// 8-bit add with carry/borrow out (registered).
module add8b (
    input  wire clk,
    input  wire rst_n,
    input  wire [7:0] a,
    input  wire [7:0] b,
    output reg  [8:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 9'd0;
        else result <= {1'b0, a} + {1'b0, b};
    end
endmodule
