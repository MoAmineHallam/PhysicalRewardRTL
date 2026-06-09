// 8-bit window comparator: in_range = (32 <= x <= 128).
module window8_32_128 (
    input  wire clk, rst_n,
    input  wire [7:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 8'd32) && (x <= 8'd128);
    end
endmodule
