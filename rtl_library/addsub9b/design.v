// 9-bit addsub with carry/borrow out (registered).
module addsub9b (
    input  wire clk,
    input  wire rst_n,
    input  wire [8:0] a,
    input  wire [8:0] b,
    input  wire sub,
    output reg  [9:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 10'd0;
        else if (sub) result <= {1'b0, a} - {1'b0, b};
        else          result <= {1'b0, a} + {1'b0, b};
    end
endmodule
