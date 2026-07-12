module sft__fir6_8b__g7 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] a0, a1, a2, a3, a4, a5;
    wire [23:0] acc = 8'd3 * a0 + 8'd5 * a1 + 8'd7 * a2 + 8'd7 * a3 + 8'd5 * a4 + 8'd3 * a5;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 8'd0; a1 <= 8'd0; a2 <= 8'd0; a3 <= 8'd0; a4 <= 8'd0; a5 <= 8'd0; y <= 16'd0;
        end else begin
            a0 <= x;
            a1 <= a0;
            a2 <= a1;
            a3 <= a2;
            a4 <= a3;
            a5 <= a4;
            y <= acc[15:0];
        end
    end
endmodule