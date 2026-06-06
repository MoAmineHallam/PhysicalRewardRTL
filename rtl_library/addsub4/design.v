// Golden reference: registered 4-bit adder/subtractor with carry/borrow out.
// Inputs: a=cnt[3:0], b=cnt[7:4], sub=cnt[8]  -> result[4:0]  (period 512, divides 1024)
// sub=0: result = a + b   (result[4] = carry-out)
// sub=1: result = a - b   (result[4] = borrow, i.e. 1 when a < b)
module addsub4 (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [3:0] a,
    input  wire [3:0] b,
    input  wire       sub,
    output reg  [4:0] result
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) result <= 5'b0;
        else if (sub) result <= {1'b0, a} - {1'b0, b};  // bit4 = borrow
        else          result <= {1'b0, a} + {1'b0, b};  // bit4 = carry
    end
endmodule
