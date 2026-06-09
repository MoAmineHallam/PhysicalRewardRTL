// 5-bit Galois LFSR. taps=0x12 seed=0x1f.
module lfsr5_1 (
    input  wire clk, rst_n,
    output reg  [4:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 5'h1f;
        else        state <= state[0] ? (({1'b0, state[4:1]}) ^ 5'h12)
                                       :  ({1'b0, state[4:1]});
    end
endmodule
