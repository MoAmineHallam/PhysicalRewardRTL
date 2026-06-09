// 5-bit left logical shift (registered). shamt 3 bits.
module logical_lsh5 (
    input  wire clk,
    input  wire rst_n,
    input  wire [4:0] data,
    input  wire [2:0] shamt,
    output reg  [4:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 5'd0;
        else        out <= data << shamt;
    end
endmodule
