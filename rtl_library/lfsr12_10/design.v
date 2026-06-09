// 12-bit Galois LFSR. taps=0x829 seed=0xabc.
module lfsr12_10 (
    input  wire clk, rst_n,
    output reg  [11:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 12'habc;
        else        state <= state[0] ? (({1'b0, state[11:1]}) ^ 12'h829)
                                       :  ({1'b0, state[11:1]});
    end
endmodule
