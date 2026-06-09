// 7-bit threshold detector: above = (x > 126) (registered).
module thresh7_126 (
    input  wire clk, rst_n,
    input  wire [6:0] x,
    output reg  above
);
    always @(posedge clk) begin
        if (!rst_n) above <= 0;
        else        above <= (x > 7'd126);
    end
endmodule
