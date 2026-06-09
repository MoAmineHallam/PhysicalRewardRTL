// 4-to-1 mux, 2-bit data (registered).
module mux4x2b (
    input  wire clk, rst_n,
    input  wire [1:0] sel,
    input wire [1:0] d0, input wire [1:0] d1, input wire [1:0] d2, input wire [1:0] d3,
    output reg  [1:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else case (sel)
            2'd0: out <= d0;
            2'd1: out <= d1;
            2'd2: out <= d2;
            2'd3: out <= d3;
            default: out <= 0;
        endcase
    end
endmodule
