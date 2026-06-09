// 4-bit threshold detector: above = (x > 12) (registered).
module thresh4_12 (
    input  wire clk, rst_n,
    input  wire [3:0] x,
    output reg  above
);
    always @(posedge clk) begin
        if (!rst_n) above <= 0;
        else        above <= (x > 4'd12);
    end
endmodule
