// 10-bit Galois LFSR. taps=0x240 seed=0x3ff.
module lfsr10_8 (
    input  wire clk, rst_n,
    output reg  [9:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 10'h3ff;
        else        state <= state[0] ? (({1'b0, state[9:1]}) ^ 10'h240)
                                       :  ({1'b0, state[9:1]});
    end
endmodule
