// 8-bit running maximum since reset.
module rmax8b (
    input  wire clk, rst_n,
    input  wire [7:0] x,
    output reg  [7:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= 0;
        else if (x > acc) acc <= x;
    end
endmodule
