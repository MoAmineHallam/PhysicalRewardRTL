// 4-bit counter wrapping at 5, tc pulses at top.
module tccnt4_5 (
    input  wire clk, rst_n,
    output reg  [3:0] count,
    output reg  tc
);
    always @(posedge clk) begin
        if (!rst_n) begin count <= 0; tc <= 0; end
        else begin
            tc <= (count == 4'd5);
            count <= (count == 4'd5) ? 4'd0 : count + 1'b1;
        end
    end
endmodule
