// 7-bit add with carry/borrow out (registered).
module add7b (
    input  wire clk,
    input  wire rst_n,
    input  wire [6:0] a,
    input  wire [6:0] b,
    output reg  [7:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 8'd0;
        else result <= {1'b0, a} + {1'b0, b};
    end
endmodule
