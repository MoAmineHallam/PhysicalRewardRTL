// 6-bit window comparator: in_range = (1 <= x <= 32).
module window6_1_32 (
    input  wire clk, rst_n,
    input  wire [5:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 6'd1) && (x <= 6'd32);
    end
endmodule
