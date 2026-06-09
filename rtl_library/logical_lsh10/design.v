// 10-bit left logical shift (registered). shamt 4 bits.
module logical_lsh10 (
    input  wire clk,
    input  wire rst_n,
    input  wire [9:0] data,
    input  wire [3:0] shamt,
    output reg  [9:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 10'd0;
        else        out <= data << shamt;
    end
endmodule
