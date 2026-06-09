// 5-bit clamp to max 30 (registered).
module clamp5_30 (
    input  wire clk, rst_n,
    input  wire [4:0] x,
    output reg  [4:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (x > 5'd30) ? 5'd30 : x;
    end
endmodule
