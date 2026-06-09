// 6-bit clamp to max 32 (registered).
module clamp6_32 (
    input  wire clk, rst_n,
    input  wire [5:0] x,
    output reg  [5:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (x > 6'd32) ? 6'd32 : x;
    end
endmodule
