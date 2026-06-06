// Golden reference: registered 8-bit logical left barrel shifter.
// Inputs: data=cnt[7:0], shamt=cnt[9:8]  -> out[7:0]  (period 1024, divides 1024)
module barrel_shift (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] data,
    input  wire [1:0] shamt,
    output reg  [7:0] out
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) out <= 8'b0;
        else        out <= data << shamt;   // logical left shift, zero-fill
    end
endmodule
