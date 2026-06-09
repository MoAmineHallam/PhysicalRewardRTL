// 6-bit Galois LFSR. taps=0x21 seed=0x3f.
module lfsr6_2 (
    input  wire clk, rst_n,
    output reg  [5:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 6'h3f;
        else        state <= state[0] ? (({1'b0, state[5:1]}) ^ 6'h21)
                                       :  ({1'b0, state[5:1]});
    end
endmodule
