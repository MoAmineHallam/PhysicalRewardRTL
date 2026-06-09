// 5-bit threshold detector: above = (x > 16) (registered).
module thresh5_16 (
    input  wire clk, rst_n,
    input  wire [4:0] x,
    output reg  above
);
    always @(posedge clk) begin
        if (!rst_n) above <= 0;
        else        above <= (x > 5'd16);
    end
endmodule
