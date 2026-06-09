// 15-bit Galois LFSR. taps=0x6000 seed=0x7fff.
module lfsr15_13 (
    input  wire clk, rst_n,
    output reg  [14:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 15'h7fff;
        else        state <= state[0] ? (({1'b0, state[14:1]}) ^ 15'h6000)
                                       :  ({1'b0, state[14:1]});
    end
endmodule
