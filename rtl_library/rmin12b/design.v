// 12-bit running minimum since reset.
module rmin12b (
    input  wire clk, rst_n,
    input  wire [11:0] x,
    output reg  [11:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= {12{1'b1}};
        else if (x < acc) acc <= x;
    end
endmodule
