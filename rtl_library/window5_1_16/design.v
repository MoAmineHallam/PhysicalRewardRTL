// 5-bit window comparator: in_range = (1 <= x <= 16).
module window5_1_16 (
    input  wire clk, rst_n,
    input  wire [4:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 5'd1) && (x <= 5'd16);
    end
endmodule
