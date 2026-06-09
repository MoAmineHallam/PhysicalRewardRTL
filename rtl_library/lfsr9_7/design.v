// 9-bit Galois LFSR. taps=0x110 seed=0x1aa.
module lfsr9_7 (
    input  wire clk, rst_n,
    output reg  [8:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 9'h1aa;
        else        state <= state[0] ? (({1'b0, state[8:1]}) ^ 9'h110)
                                       :  ({1'b0, state[8:1]});
    end
endmodule
