// 5-bit window comparator: in_range = (8 <= x <= 31).
module window5_8_31 (
    input  wire clk, rst_n,
    input  wire [4:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 5'd8) && (x <= 5'd31);
    end
endmodule
