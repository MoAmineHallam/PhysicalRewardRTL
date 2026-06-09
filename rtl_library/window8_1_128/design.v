// 8-bit window comparator: in_range = (1 <= x <= 128).
module window8_1_128 (
    input  wire clk, rst_n,
    input  wire [7:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 8'd1) && (x <= 8'd128);
    end
endmodule
