// 4-bit clamp to max 8 (registered).
module clamp4_8 (
    input  wire clk, rst_n,
    input  wire [3:0] x,
    output reg  [3:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (x > 4'd8) ? 4'd8 : x;
    end
endmodule
