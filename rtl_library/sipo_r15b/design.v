// 15-bit serial-in parallel-out shift register (right).
module sipo_r15b (
    input  wire clk, rst_n,
    input  wire sin,
    output reg  [14:0] q
);
    always @(posedge clk) begin
        if (!rst_n) q <= 0;
        else        q <= {sin, q[14:1]};
    end
endmodule
