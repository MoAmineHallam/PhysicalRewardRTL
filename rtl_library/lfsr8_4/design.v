// 8-bit Galois LFSR. taps=0x8e seed=0xac.
module lfsr8_4 (
    input  wire clk, rst_n,
    output reg  [7:0] state
);
    always @(posedge clk) begin
        if (!rst_n) state <= 8'hac;
        else        state <= state[0] ? (({1'b0, state[7:1]}) ^ 8'h8e)
                                       :  ({1'b0, state[7:1]});
    end
endmodule
