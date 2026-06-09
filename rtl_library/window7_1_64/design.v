// 7-bit window comparator: in_range = (1 <= x <= 64).
module window7_1_64 (
    input  wire clk, rst_n,
    input  wire [6:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 7'd1) && (x <= 7'd64);
    end
endmodule
