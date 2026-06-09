// 5-bit threshold detector: above = (x > 24) (registered).
module thresh5_24 (
    input  wire clk, rst_n,
    input  wire [4:0] x,
    output reg  above
);
    always @(posedge clk) begin
        if (!rst_n) above <= 0;
        else        above <= (x > 5'd24);
    end
endmodule
