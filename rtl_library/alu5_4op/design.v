// 5-bit ALU, 4 ops selected by op[1:0] (registered).
module alu5_4op (
    input  wire clk, rst_n,
    input  wire [4:0] a,
    input  wire [4:0] b,
    input  wire [1:0] op,
    output reg  [4:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 0;
        else case (op)
            2'd0: result <= a + b;
            2'd1: result <= a - b;
            2'd2: result <= a & b;
            2'd3: result <= a | b;
            default: result <= 0;
        endcase
    end
endmodule
