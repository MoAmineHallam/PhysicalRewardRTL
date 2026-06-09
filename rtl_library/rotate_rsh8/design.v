// 8-bit right rotate shift (registered). shamt 3 bits.
module rotate_rsh8 (
    input  wire clk,
    input  wire rst_n,
    input  wire [7:0] data,
    input  wire [2:0] shamt,
    output reg  [7:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 8'd0;
        else        out <= (shamt == 0) ? data : ((data >> shamt) | (data << (8 - shamt)));
    end
endmodule
