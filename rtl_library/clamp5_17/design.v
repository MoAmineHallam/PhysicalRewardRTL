// 5-bit clamp to max 17 (registered).
module clamp5_17 (
    input  wire clk, rst_n,
    input  wire [4:0] x,
    output reg  [4:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (x > 5'd17) ? 5'd17 : x;
    end
endmodule
