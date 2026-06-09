// 5-bit window comparator: in_range = (10 <= x <= 21).
module window5_10_21 (
    input  wire clk, rst_n,
    input  wire [4:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 5'd10) && (x <= 5'd21);
    end
endmodule
