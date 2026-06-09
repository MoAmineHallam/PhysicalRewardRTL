// 6-bit ALU, 8 ops selected by op[2:0] (registered).
module alu6_8op (
    input  wire clk, rst_n,
    input  wire [5:0] a,
    input  wire [5:0] b,
    input  wire [2:0] op,
    output reg  [5:0] result
);
    always @(posedge clk) begin
        if (!rst_n) result <= 0;
        else case (op)
            3'd0: result <= a + b;
            3'd1: result <= a - b;
            3'd2: result <= a & b;
            3'd3: result <= a | b;
            3'd4: result <= a ^ b;
            3'd5: result <= ~a;
            3'd6: result <= a << 1;
            3'd7: result <= a >> 1;
            default: result <= 0;
        endcase
    end
endmodule
