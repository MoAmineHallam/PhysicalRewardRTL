// 6-bit clamp to max 48 (registered).
module clamp6_48 (
    input  wire clk, rst_n,
    input  wire [5:0] x,
    output reg  [5:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (x > 6'd48) ? 6'd48 : x;
    end
endmodule
