// 4-bit right logical shift (registered). shamt 2 bits.
module logical_rsh4 (
    input  wire clk,
    input  wire rst_n,
    input  wire [3:0] data,
    input  wire [1:0] shamt,
    output reg  [3:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 4'd0;
        else        out <= data >> shamt;
    end
endmodule
