// 11-bit Galois LFSR. taps=0x500 seed=0x7ab.
module lfsr11_9 (
    input  wire clk, rst_n,
    output reg  [10:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 11'h7ab;
        else        state <= state[0] ? (({1'b0, state[10:1]}) ^ 11'h500)
                                       :  ({1'b0, state[10:1]});
    end
endmodule
