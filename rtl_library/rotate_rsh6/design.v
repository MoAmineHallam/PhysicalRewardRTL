// 6-bit right rotate shift (registered). shamt 3 bits.
module rotate_rsh6 (
    input  wire clk,
    input  wire rst_n,
    input  wire [5:0] data,
    input  wire [2:0] shamt,
    output reg  [5:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 6'd0;
        else        out <= (shamt == 0) ? data : ((data >> shamt) | (data << (6 - shamt)));
    end
endmodule
