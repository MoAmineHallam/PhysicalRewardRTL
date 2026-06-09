// 4-bit threshold detector: above = (x > 8) (registered).
module thresh4_8 (
    input  wire clk, rst_n,
    input  wire [3:0] x,
    output reg  above
);
    always @(posedge clk) begin
        if (!rst_n) above <= 0;
        else        above <= (x > 4'd8);
    end
endmodule
