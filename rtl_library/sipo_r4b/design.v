// 4-bit serial-in parallel-out shift register (right).
module sipo_r4b (
    input  wire clk, rst_n,
    input  wire sin,
    output reg  [3:0] q
);
    always @(posedge clk) begin
        if (!rst_n) q <= 0;
        else        q <= {sin, q[3:1]};
    end
endmodule
