// 5-bit counter wrapping at 10, tc pulses at top.
module tccnt5_10 (
    input  wire clk, rst_n,
    output reg  [4:0] count,
    output reg  tc
);
    always @(posedge clk) begin
        if (!rst_n) begin count <= 0; tc <= 0; end
        else begin
            tc <= (count == 5'd10);
            count <= (count == 5'd10) ? 5'd0 : count + 1'b1;
        end
    end
endmodule
