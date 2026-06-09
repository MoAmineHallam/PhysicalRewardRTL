// 16-bit accumulator of 6-bit input (registered, wraps).
module acc6to16 (
    input  wire clk, rst_n,
    input  wire [5:0] data,
    output reg  [15:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= 0;
        else        acc <= acc + data;
    end
endmodule
