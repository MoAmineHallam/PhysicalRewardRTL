// 8-bit accumulator of 3-bit input (registered, wraps).
module acc3to8 (
    input  wire clk, rst_n,
    input  wire [2:0] data,
    output reg  [7:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= 0;
        else        acc <= acc + data;
    end
endmodule
