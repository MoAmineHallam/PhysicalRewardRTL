// 3-bit serial-in parallel-out shift register (left).
module sipo_l3b (
    input  wire clk, rst_n,
    input  wire sin,
    output reg  [2:0] q
);
    always @(posedge clk) begin
        if (!rst_n) q <= 0;
        else        q <= {q[1:0], sin};
    end
endmodule
