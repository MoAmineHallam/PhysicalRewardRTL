// 8-bit Galois LFSR. taps=0xb8 seed=0xff.
module lfsr8_6 (
    input  wire clk, rst_n,
    output reg  [7:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 8'hff;
        else        state <= state[0] ? (({1'b0, state[7:1]}) ^ 8'hb8)
                                       :  ({1'b0, state[7:1]});
    end
endmodule
