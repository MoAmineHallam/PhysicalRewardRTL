// 8-bit threshold detector: above = (x > 254) (registered).
module thresh8_254 (
    input  wire clk, rst_n,
    input  wire [7:0] x,
    output reg  above
);
    always @(posedge clk) begin
        if (!rst_n) above <= 0;
        else        above <= (x > 8'd254);
    end
endmodule
