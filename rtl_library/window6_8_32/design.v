// 6-bit window comparator: in_range = (8 <= x <= 32).
module window6_8_32 (
    input  wire clk, rst_n,
    input  wire [5:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 6'd8) && (x <= 6'd32);
    end
endmodule
