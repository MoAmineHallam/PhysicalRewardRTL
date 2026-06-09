// 7-bit clamp to max 65 (registered).
module clamp7_65 (
    input  wire clk, rst_n,
    input  wire [6:0] x,
    output reg  [6:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (x > 7'd65) ? 7'd65 : x;
    end
endmodule
