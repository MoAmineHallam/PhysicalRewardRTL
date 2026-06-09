// 15-bit sub with carry/borrow out (registered).
module sub15b (
    input  wire clk,
    input  wire rst_n,
    input  wire [14:0] a,
    input  wire [14:0] b,
    output reg  [15:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 16'd0;
        else result <= {1'b0, a} - {1'b0, b};
    end
endmodule
