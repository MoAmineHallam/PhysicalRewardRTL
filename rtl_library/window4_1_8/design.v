// 4-bit window comparator: in_range = (1 <= x <= 8).
module window4_1_8 (
    input  wire clk, rst_n,
    input  wire [3:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 4'd1) && (x <= 4'd8);
    end
endmodule
