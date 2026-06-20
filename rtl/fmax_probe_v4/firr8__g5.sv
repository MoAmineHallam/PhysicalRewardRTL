module firr8__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] a0, a1, a2, a3, a4, a5, a6, a7;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 8'd0; a1 <= 8'd0; a2 <= 8'd0; a3 <= 8'd0; a4 <= 8'd0; a5 <= 8'd0; a6 <= 8'd0; a7 <= 8'd0; y <= 16'd0;
        end else begin
            a0 <= x;
            a1 <= a0;
            a2 <= a1;
            a3 <= a2;
            a4 <= a3;
            a5 <= a4;
            a6 <= a5;
            a7 <= a6;
            y <= (1'd1 * a0) + (2'd2 * a1) + (3'd3 * a2) + (4'd4 * a3) + (5'd5 * a4) + (6'd6 * a5) + (7'd7 * a6) + (8'd8 * a7);
        end
    end
endmodule