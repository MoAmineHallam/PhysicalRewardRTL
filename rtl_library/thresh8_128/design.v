// 8-bit threshold detector: above = (x > 128) (registered).
module thresh8_128 (
    input  wire clk, rst_n,
    input  wire [7:0] x,
    output reg  above
);
    always @(posedge clk) begin
        if (!rst_n) above <= 0;
        else        above <= (x > 8'd128);
    end
endmodule
