// 11-bit serial-in parallel-out shift register (right).
module sipo_r11b (
    input  wire clk, rst_n,
    input  wire sin,
    output reg  [10:0] q
);
    always @(posedge clk) begin
        if (!rst_n) q <= 0;
        else        q <= {sin, q[10:1]};
    end
endmodule
