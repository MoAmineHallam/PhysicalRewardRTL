// 8-bit Galois LFSR. Polynomial: x^8 + x^6 + x^5 + x^4 + 1.
// Tap mask 8'h70 (bits 6,5,4). Seed = 8'hAC on reset.
// No external inputs. Period = 255.
module lfsr8 (
    input  wire       clk,
    input  wire       rst_n,
    output reg  [7:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 8'hAC;
        else        state <= {1'b0, state[7:1]} ^ (state[0] ? 8'h70 : 8'h00);
    end
endmodule
