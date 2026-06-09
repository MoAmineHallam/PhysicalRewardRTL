// 4-bit clamp to max 12 (registered).
module clamp4_12 (
    input  wire clk, rst_n,
    input  wire [3:0] x,
    output reg  [3:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (x > 4'd12) ? 4'd12 : x;
    end
endmodule
