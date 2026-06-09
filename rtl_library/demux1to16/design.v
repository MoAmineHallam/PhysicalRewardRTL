// 1-to-16 demux: out[sel] = din, others 0 (registered).
module demux1to16 (
    input  wire clk, rst_n,
    input  wire din,
    input  wire [3:0] sel,
    output reg  [15:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= din ? (16'd1 << sel) : 16'd0;
    end
endmodule
