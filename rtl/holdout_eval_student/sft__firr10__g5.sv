module sft__firr10__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0, a1, a2, a3, a4, a5, a6, a7, a8, a9;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 24'd0;
            a1 <= 24'd0;
            a2 <= 24'd0;
            a3 <= 24'd0;
            a4 <= 24'd0;
            a5 <= 24'd0;
            a6 <= 24'd0;
            a7 <= 24'd0;
            a8 <= 24'd0;
            a9 <= 24'd0;
            y <= 16'd0;
        end else begin
            a0 <= (8'd1) * x + a1;
            a1 <= (8'd2) * x + a2;
            a2 <= (8'd3) * x + a3;
            a3 <= (8'd4) * x + a4;
            a4 <= (8'd5) * x + a5;
            a5 <= (8'd6) * x + a6;
            a6 <= (8'd7) * x + a7;
            a7 <= (8'd8) * x + a8;
            a8 <= (8'd9) * x + a9;
            a9 <= (8'd10) * x;
            y <= a0[15:0];
        end
    end
endmodule