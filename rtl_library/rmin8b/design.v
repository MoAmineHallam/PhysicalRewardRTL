// 8-bit running minimum since reset.
module rmin8b (
    input  wire clk, rst_n,
    input  wire [7:0] x,
    output reg  [7:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= {8{1'b1}};
        else if (x < acc) acc <= x;
    end
endmodule
