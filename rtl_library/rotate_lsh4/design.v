// 4-bit left rotate shift (registered). shamt 2 bits.
module rotate_lsh4 (
    input  wire clk,
    input  wire rst_n,
    input  wire [3:0] data,
    input  wire [1:0] shamt,
    output reg  [3:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 4'd0;
        else        out <= (shamt == 0) ? data : ((data << shamt) | (data >> (4 - shamt)));
    end
endmodule
