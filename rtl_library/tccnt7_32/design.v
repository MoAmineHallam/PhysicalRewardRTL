// 7-bit counter wrapping at 32, tc pulses at top.
module tccnt7_32 (
    input  wire clk, rst_n,
    output reg  [6:0] count,
    output reg  tc
);
    always @(posedge clk) begin
        if (!rst_n) begin count <= 0; tc <= 0; end
        else begin
            tc <= (count == 7'd32);
            count <= (count == 7'd32) ? 7'd0 : count + 1'b1;
        end
    end
endmodule
