// 6-bit counter wrapping at 48, tc pulses at top.
module tccnt6_48 (
    input  wire clk, rst_n,
    output reg  [5:0] count,
    output reg  tc
);
    always @(posedge clk) begin
        if (!rst_n) begin count <= 0; tc <= 0; end
        else begin
            tc <= (count == 6'd48);
            count <= (count == 6'd48) ? 6'd0 : count + 1'b1;
        end
    end
endmodule
