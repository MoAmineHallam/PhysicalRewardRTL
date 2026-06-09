// 5-bit ALU, 2 ops selected by op[0:0] (registered).
module alu5_2op (
    input  wire clk, rst_n,
    input  wire [4:0] a,
    input  wire [4:0] b,
    input  wire [0:0] op,
    output reg  [4:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 0;
        else case (op)
            1'd0: result <= a + b;
            1'd1: result <= a - b;
            default: result <= 0;
        endcase
    end
endmodule
