// 13-bit sub with carry/borrow out (registered).
module sub13b (
    input  wire clk,
    input  wire rst_n,
    input  wire [12:0] a,
    input  wire [12:0] b,
    output reg  [13:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 14'd0;
        else result <= {1'b0, a} - {1'b0, b};
    end
endmodule
