// 3-bit addsub with carry/borrow out (registered).
module addsub3b (
    input  wire clk,
    input  wire rst_n,
    input  wire [2:0] a,
    input  wire [2:0] b,
    input  wire sub,
    output reg  [3:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 4'd0;
        else if (sub) result <= {1'b0, a} - {1'b0, b};
        else          result <= {1'b0, a} + {1'b0, b};
    end
endmodule
