// 7-bit window comparator: in_range = (32 <= x <= 96).
module window7_32_96 (
    input  wire clk, rst_n,
    input  wire [6:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 7'd32) && (x <= 7'd96);
    end
endmodule
