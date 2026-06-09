// 1-to-8 demux: out[sel] = din, others 0 (registered).
module demux1to8 (
    input  wire clk, rst_n,
    input  wire din,
    input  wire [2:0] sel,
    output reg  [7:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= din ? (8'd1 << sel) : 8'd0;
    end
endmodule
