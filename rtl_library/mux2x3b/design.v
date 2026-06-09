// 2-to-1 mux, 3-bit data (registered).
module mux2x3b (
    input  wire clk, rst_n,
    input  wire [0:0] sel,
    input wire [2:0] d0, input wire [2:0] d1,
    output reg  [2:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else case (sel)
            1'd0: out <= d0;
            1'd1: out <= d1;
            default: out <= 0;
        endcase
    end
endmodule
