// 16-to-1 mux, 1-bit data (registered).
module mux16x1b (
    input  wire clk, rst_n,
    input  wire [3:0] sel,
    input wire [0:0] d0, input wire [0:0] d1, input wire [0:0] d2, input wire [0:0] d3, input wire [0:0] d4, input wire [0:0] d5, input wire [0:0] d6, input wire [0:0] d7, input wire [0:0] d8, input wire [0:0] d9, input wire [0:0] d10, input wire [0:0] d11, input wire [0:0] d12, input wire [0:0] d13, input wire [0:0] d14, input wire [0:0] d15,
    output reg  [0:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else case (sel)
            4'd0: out <= d0;
            4'd1: out <= d1;
            4'd2: out <= d2;
            4'd3: out <= d3;
            4'd4: out <= d4;
            4'd5: out <= d5;
            4'd6: out <= d6;
            4'd7: out <= d7;
            4'd8: out <= d8;
            4'd9: out <= d9;
            4'd10: out <= d10;
            4'd11: out <= d11;
            4'd12: out <= d12;
            4'd13: out <= d13;
            4'd14: out <= d14;
            4'd15: out <= d15;
            default: out <= 0;
        endcase
    end
endmodule
