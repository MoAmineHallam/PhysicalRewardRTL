// 10-bit running minimum since reset.
module rmin10b (
    input  wire clk, rst_n,
    input  wire [9:0] x,
    output reg  [9:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= {10{1'b1}};
        else if (x < acc) acc <= x;
    end
endmodule
