// 12-bit left logical shift (registered). shamt 4 bits.
module logical_lsh12 (
    input  wire clk,
    input  wire rst_n,
    input  wire [11:0] data,
    input  wire [3:0] shamt,
    output reg  [11:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 12'd0;
        else        out <= data << shamt;
    end
endmodule
