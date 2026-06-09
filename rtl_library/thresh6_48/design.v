// 6-bit threshold detector: above = (x > 48) (registered).
module thresh6_48 (
    input  wire clk, rst_n,
    input  wire [5:0] x,
    output reg  above
);
    always @(posedge clk) begin
        if (!rst_n) above <= 0;
        else        above <= (x > 6'd48);
    end
endmodule
