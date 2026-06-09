// 8-bit clamp to max 254 (registered).
module clamp8_254 (
    input  wire clk, rst_n,
    input  wire [7:0] x,
    output reg  [7:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (x > 8'd254) ? 8'd254 : x;
    end
endmodule
