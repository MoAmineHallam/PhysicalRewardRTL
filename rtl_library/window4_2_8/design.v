// 4-bit window comparator: in_range = (2 <= x <= 8).
module window4_2_8 (
    input  wire clk, rst_n,
    input  wire [3:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 4'd2) && (x <= 4'd8);
    end
endmodule
