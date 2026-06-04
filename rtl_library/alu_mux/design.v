// Golden reference: registered ALU with op-select mux
// op: 0=ADD 1=SUB 2=AND 3=OR 4=XOR 5=NOT_A 6=PASS_A 7=PASS_B
module alu_mux (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [3:0] a,
    input  wire [3:0] b,
    input  wire [2:0] op,
    output reg  [3:0] result
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            result <= 4'b0;
        else
            case (op)
                3'd0: result <= a + b;
                3'd1: result <= a - b;
                3'd2: result <= a & b;
                3'd3: result <= a | b;
                3'd4: result <= a ^ b;
                3'd5: result <= ~a;
                3'd6: result <= a;
                3'd7: result <= b;
            endcase
    end
endmodule
