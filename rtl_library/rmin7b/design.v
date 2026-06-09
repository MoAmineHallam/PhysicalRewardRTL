// 7-bit running minimum since reset.
module rmin7b (
    input  wire clk, rst_n,
    input  wire [6:0] x,
    output reg  [6:0] acc
);
    always @(posedge clk) begin
        if (!rst_n) acc <= {7{1'b1}};
        else if (x < acc) acc <= x;
    end
endmodule
