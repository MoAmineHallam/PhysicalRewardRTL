// 8-bit counter wrapping at 192, tc pulses at top.
module tccnt8_192 (
    input  wire clk, rst_n,
    output reg  [7:0] count,
    output reg  tc
);
    always @(posedge clk) begin
        if (!rst_n) begin count <= 0; tc <= 0; end
        else begin
            tc <= (count == 8'd192);
            count <= (count == 8'd192) ? 8'd0 : count + 1'b1;
        end
    end
endmodule
