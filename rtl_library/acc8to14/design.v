// 14-bit accumulator of 8-bit input (registered, wraps).
module acc8to14 (
    input  wire clk, rst_n,
    input  wire [7:0] data,
    output reg  [13:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= 0;
        else        acc <= acc + data;
    end
endmodule
