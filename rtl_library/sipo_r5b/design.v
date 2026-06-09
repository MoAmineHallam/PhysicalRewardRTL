// 5-bit serial-in parallel-out shift register (right).
module sipo_r5b (
    input  wire clk, rst_n,
    input  wire sin,
    output reg  [4:0] q
);
    always @(posedge clk) begin
        if (!rst_n) q <= 0;
        else        q <= {sin, q[4:1]};
    end
endmodule
