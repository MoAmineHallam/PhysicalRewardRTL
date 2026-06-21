module fir4_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  a1, a2, a3, a4;
    wire [23:0] acc = 8'd3 * a1 + 8'd5 * a2 + 8'd5 * a3 + 8'd3 * a4;
    always @(posedge clk) begin
        if (!rst_n) begin
            a1 <= 8'd0; a2 <= 8'd0; a3 <= 8'd0; a4 <= 8'd0; y <= 16'd0;
        end else begin
            a1 <= x;
            a2 <= a1;
            a3 <= a2;
            a4 <= a3;
            y <= acc[15:0];
        end
    end
endmodule