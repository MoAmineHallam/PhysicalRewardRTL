// 16-bit accumulator of 5-bit input (registered, wraps).
module acc5to16 (
    input  wire clk, rst_n,
    input  wire [4:0] data,
    output reg  [15:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= 0;
        else        acc <= acc + data;
    end
endmodule
