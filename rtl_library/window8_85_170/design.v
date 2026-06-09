// 8-bit window comparator: in_range = (85 <= x <= 170).
module window8_85_170 (
    input  wire clk, rst_n,
    input  wire [7:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 8'd85) && (x <= 8'd170);
    end
endmodule
