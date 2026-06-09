// 7-bit window comparator: in_range = (42 <= x <= 85).
module window7_42_85 (
    input  wire clk, rst_n,
    input  wire [6:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 7'd42) && (x <= 7'd85);
    end
endmodule
