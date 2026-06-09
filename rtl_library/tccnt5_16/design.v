// 5-bit counter wrapping at 16, tc pulses at top.
module tccnt5_16 (
    input  wire clk, rst_n,
    output reg  [4:0] count,
    output reg  tc
);
    always @(posedge clk) begin
        if (!rst_n) begin count <= 0; tc <= 0; end
        else begin
            tc <= (count == 5'd16);
            count <= (count == 5'd16) ? 5'd0 : count + 1'b1;
        end
    end
endmodule
