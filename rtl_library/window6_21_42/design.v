// 6-bit window comparator: in_range = (21 <= x <= 42).
module window6_21_42 (
    input  wire clk, rst_n,
    input  wire [5:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 6'd21) && (x <= 6'd42);
    end
endmodule
