// 4-bit running minimum since reset.
module rmin4b (
    input  wire clk, rst_n,
    input  wire [3:0] x,
    output reg  [3:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= {4{1'b1}};
        else if (x < acc) acc <= x;
    end
endmodule
