// 8-bit window comparator: in_range = (64 <= x <= 255).
module window8_64_255 (
    input  wire clk, rst_n,
    input  wire [7:0] x,
    output reg  in_range
);
    always @(posedge clk) begin
        if (!rst_n) in_range <= 0;
        else        in_range <= (x >= 8'd64) && (x <= 8'd255);
    end
endmodule
