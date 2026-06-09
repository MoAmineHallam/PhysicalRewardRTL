// 5-bit running minimum since reset.
module rmin5b (
    input  wire clk, rst_n,
    input  wire [4:0] x,
    output reg  [4:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= {5{1'b1}};
        else if (x < acc) acc <= x;
    end
endmodule
