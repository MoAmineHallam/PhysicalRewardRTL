// 6-bit threshold detector: above = (x > 62) (registered).
module thresh6_62 (
    input  wire clk, rst_n,
    input  wire [5:0] x,
    output reg  above
);
    always @(posedge clk) begin
        if (!rst_n) above <= 0;
        else        above <= (x > 6'd62);
    end
endmodule
