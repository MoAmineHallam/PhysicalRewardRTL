// 1-to-2 demux: out[sel] = din, others 0 (registered).
module demux1to2 (
    input  wire clk, rst_n,
    input  wire din,
    input  wire [0:0] sel,
    output reg  [1:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= din ? (2'd1 << sel) : 2'd0;
    end
endmodule
