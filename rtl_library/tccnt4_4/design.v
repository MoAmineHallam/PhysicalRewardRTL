// 4-bit counter wrapping at 4, tc pulses at top.
module tccnt4_4 (
    input  wire clk, rst_n,
    output reg  [3:0] count,
    output reg  tc
);
    always @(posedge clk) begin
        if (!rst_n) begin count <= 0; tc <= 0; end
        else begin
            tc <= (count == 4'd4);
            count <= (count == 4'd4) ? 4'd0 : count + 1'b1;
        end
    end
endmodule
