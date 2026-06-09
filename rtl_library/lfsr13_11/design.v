// 13-bit Galois LFSR. taps=0x100d seed=0x1fff.
module lfsr13_11 (
    input  wire clk, rst_n,
    output reg  [12:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 13'h1fff;
        else        state <= state[0] ? (({1'b0, state[12:1]}) ^ 13'h100d)
                                       :  ({1'b0, state[12:1]});
    end
endmodule
