// 9-bit serial-in parallel-out shift register (left).
module sipo_l9b (
    input  wire clk, rst_n,
    input  wire sin,
    output reg  [8:0] q
);
    always @(posedge clk) begin
        if (!rst_n) q <= 0;
        else        q <= {q[7:0], sin};
    end
endmodule
