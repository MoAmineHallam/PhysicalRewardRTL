// 7-bit window comparator: in_range = (16 <= x <= 64).
module window7_16_64 (
    input  wire clk, rst_n,
    input  wire [6:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 7'd16) && (x <= 7'd64);
    end
endmodule
