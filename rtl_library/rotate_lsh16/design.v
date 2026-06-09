// 16-bit left rotate shift (registered). shamt 4 bits.
module rotate_lsh16 (
    input  wire clk,
    input  wire rst_n,
    input  wire [15:0] data,
    input  wire [3:0] shamt,
    output reg  [15:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 16'd0;
        else        out <= (shamt == 0) ? data : ((data << shamt) | (data >> (16 - shamt)));
    end
endmodule
