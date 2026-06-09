// 8-to-1 mux, 3-bit data (registered).
module mux8x3b (
    input  wire clk, rst_n,
    input  wire [2:0] sel,
    input wire [2:0] d0, input wire [2:0] d1, input wire [2:0] d2, input wire [2:0] d3, input wire [2:0] d4, input wire [2:0] d5, input wire [2:0] d6, input wire [2:0] d7,
    output reg  [2:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else case (sel)
            3'd0: out <= d0;
            3'd1: out <= d1;
            3'd2: out <= d2;
            3'd3: out <= d3;
            3'd4: out <= d4;
            3'd5: out <= d5;
            3'd6: out <= d6;
            3'd7: out <= d7;
            default: out <= 0;
        endcase
    end
endmodule
