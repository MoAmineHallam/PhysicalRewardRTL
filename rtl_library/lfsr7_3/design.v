// 7-bit Galois LFSR. taps=0x41 seed=0x7f.
module lfsr7_3 (
    input  wire clk, rst_n,
    output reg  [6:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 7'h7f;
        else        state <= state[0] ? (({1'b0, state[6:1]}) ^ 7'h41)
                                       :  ({1'b0, state[6:1]});
    end
endmodule
