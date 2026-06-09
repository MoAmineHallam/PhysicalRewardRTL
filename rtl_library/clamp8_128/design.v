// 8-bit clamp to max 128 (registered).
module clamp8_128 (
    input  wire clk, rst_n,
    input  wire [7:0] x,
    output reg  [7:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (x > 8'd128) ? 8'd128 : x;
    end
endmodule
