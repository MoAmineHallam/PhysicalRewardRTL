// 7-bit right rotate shift (registered). shamt 3 bits.
module rotate_rsh7 (
    input  wire clk,
    input  wire rst_n,
    input  wire [6:0] data,
    input  wire [2:0] shamt,
    output reg  [6:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 7'd0;
        else        out <= (shamt == 0) ? data : ((data >> shamt) | (data << (7 - shamt)));
    end
endmodule
