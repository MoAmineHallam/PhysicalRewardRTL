// Registered 4-to-1 mux with 4-bit data paths.
// For counter-driven testing: sel=cnt[1:0], d0=cnt[5:2], d1=cnt[9:6], d2=cnt[13:10], d3=cnt[17:14]
module mux4to1 (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [3:0] d0,
    input  wire [3:0] d1,
    input  wire [3:0] d2,
    input  wire [3:0] d3,
    input  wire [1:0] sel,
    output reg  [3:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 4'b0;
        else case (sel)
            2'd0: out <= d0;
            2'd1: out <= d1;
            2'd2: out <= d2;
            2'd3: out <= d3;
        endcase
    end
endmodule
