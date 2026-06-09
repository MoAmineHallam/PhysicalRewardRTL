// 7-bit addsub with carry/borrow out (registered).
module addsub7b (
    input  wire clk,
    input  wire rst_n,
    input  wire [6:0] a,
    input  wire [6:0] b,
    input  wire sub,
    output reg  [7:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 8'd0;
        else if (sub) result <= {1'b0, a} - {1'b0, b};
        else          result <= {1'b0, a} + {1'b0, b};
    end
endmodule
