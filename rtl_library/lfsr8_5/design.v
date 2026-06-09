// 8-bit Galois LFSR. taps=0x95 seed=0x1.
module lfsr8_5 (
    input  wire clk, rst_n,
    output reg  [7:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 8'h1;
        else        state <= state[0] ? (({1'b0, state[7:1]}) ^ 8'h95)
                                       :  ({1'b0, state[7:1]});
    end
endmodule
