// 10-bit right rotate shift (registered). shamt 4 bits.
module rotate_rsh10 (
    input  wire clk,
    input  wire rst_n,
    input  wire [9:0] data,
    input  wire [3:0] shamt,
    output reg  [9:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 10'd0;
        else        out <= (shamt == 0) ? data : ((data >> shamt) | (data << (10 - shamt)));
    end
endmodule
