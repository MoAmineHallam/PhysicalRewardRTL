// 7-bit clamp to max 126 (registered).
module clamp7_126 (
    input  wire clk, rst_n,
    input  wire [6:0] x,
    output reg  [6:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (x > 7'd126) ? 7'd126 : x;
    end
endmodule
