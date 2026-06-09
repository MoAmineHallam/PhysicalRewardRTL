// 7-bit threshold detector: above = (x > 32) (registered).
module thresh7_32 (
    input  wire clk, rst_n,
    input  wire [6:0] x,
    output reg  above
);
    always @(posedge clk) begin
        if (!rst_n) above <= 0;
        else        above <= (x > 7'd32);
    end
endmodule
