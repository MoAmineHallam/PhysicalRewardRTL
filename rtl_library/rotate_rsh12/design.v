// 12-bit right rotate shift (registered). shamt 4 bits.
module rotate_rsh12 (
    input  wire clk,
    input  wire rst_n,
    input  wire [11:0] data,
    input  wire [3:0] shamt,
    output reg  [11:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 12'd0;
        else        out <= (shamt == 0) ? data : ((data >> shamt) | (data << (12 - shamt)));
    end
endmodule
