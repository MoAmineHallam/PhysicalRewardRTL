// 4-bit Galois LFSR. taps=0x9 seed=0xf.
module lfsr4_0 (
    input  wire clk, rst_n,
    output reg  [3:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 4'hf;
        else        state <= state[0] ? (({1'b0, state[3:1]}) ^ 4'h9)
                                       :  ({1'b0, state[3:1]});
    end
endmodule
