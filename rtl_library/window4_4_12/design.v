// 4-bit window comparator: in_range = (4 <= x <= 12).
module window4_4_12 (
    input  wire clk, rst_n,
    input  wire [3:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 4'd4) && (x <= 4'd12);
    end
endmodule
