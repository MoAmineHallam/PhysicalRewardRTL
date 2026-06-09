// 1-to-4 demux: out[sel] = din, others 0 (registered).
module demux1to4 (
    input  wire clk, rst_n,
    input  wire din,
    input  wire [1:0] sel,
    output reg  [3:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= din ? (4'd1 << sel) : 4'd0;
    end
endmodule
