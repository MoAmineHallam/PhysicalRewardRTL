// 16-bit Galois LFSR. taps=0xb400 seed=0xace1.
module lfsr16_14 (
    input  wire clk, rst_n,
    output reg  [15:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 16'hace1;
        else        state <= state[0] ? (({1'b0, state[15:1]}) ^ 16'hb400)
                                       :  ({1'b0, state[15:1]});
    end
endmodule
