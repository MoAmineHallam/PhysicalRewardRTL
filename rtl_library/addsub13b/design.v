// 13-bit addsub with carry/borrow out (registered).
module addsub13b (
    input  wire clk,
    input  wire rst_n,
    input  wire [12:0] a,
    input  wire [12:0] b,
    input  wire sub,
    output reg  [13:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 14'd0;
        else if (sub) result <= {1'b0, a} - {1'b0, b};
        else          result <= {1'b0, a} + {1'b0, b};
    end
endmodule
