// 14-bit Galois LFSR. taps=0x2015 seed=0x2abc.
module lfsr14_12 (
    input  wire clk, rst_n,
    output reg  [13:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 14'h2abc;
        else        state <= state[0] ? (({1'b0, state[13:1]}) ^ 14'h2015)
                                       :  ({1'b0, state[13:1]});
    end
endmodule
