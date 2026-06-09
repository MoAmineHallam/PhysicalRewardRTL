// 6-bit window comparator: in_range = (16 <= x <= 63).
module window6_16_63 (
    input  wire clk, rst_n,
    input  wire [5:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 6'd16) && (x <= 6'd63);
    end
endmodule
