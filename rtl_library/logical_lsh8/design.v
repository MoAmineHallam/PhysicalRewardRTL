// 8-bit left logical shift (registered). shamt 3 bits.
module logical_lsh8 (
    input  wire clk,
    input  wire rst_n,
    input  wire [7:0] data,
    input  wire [2:0] shamt,
    output reg  [7:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 8'd0;
        else        out <= data << shamt;
    end
endmodule
