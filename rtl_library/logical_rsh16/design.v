// 16-bit right logical shift (registered). shamt 4 bits.
module logical_rsh16 (
    input  wire clk,
    input  wire rst_n,
    input  wire [15:0] data,
    input  wire [3:0] shamt,
    output reg  [15:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 16'd0;
        else        out <= data >> shamt;
    end
endmodule
