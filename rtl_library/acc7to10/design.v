// 10-bit accumulator of 7-bit input (registered, wraps).
module acc7to10 (
    input  wire clk, rst_n,
    input  wire [6:0] data,
    output reg  [9:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= 0;
        else        acc <= acc + data;
    end
endmodule
