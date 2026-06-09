// 6-bit serial-in parallel-out shift register (right).
module sipo_r6b (
    input  wire clk, rst_n,
    input  wire sin,
    output reg  [5:0] q
);
    always @(posedge clk) begin
        if (!rst_n) q <= 0;
        else        q <= {sin, q[5:1]};
    end
endmodule
