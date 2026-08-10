module grpo__fir18_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 'd0; a1 <= 'd0; a2 <= 'd0; a3 <= 'd0; a4 <= 'd0; a5 <= 'd0; a6 <= 'd0; a7 <= 'd0; a8 <= 'd0; a9 <= 'd0; a10 <= 'd0; a11 <= 'd0; a12 <= 'd0; a13 <= 'd0; a14 <= 'd0; a15 <= 'd0; a16 <= 'd0; a17 <= 'd0; y <= 'd0;
        end else begin
            a0 <= ($signed(x) * 8'd3) + a1;
            a1 <= ($signed(x) * 8'd5) + a2;
            a2 <= ($signed(x) * 8'd7) + a3;
            a3 <= ($signed(x) * 8'd9) + a4;
            a4 <= ($signed(x) * 8'd11) + a5;
            a5 <= ($signed(x) * 8'd13) + a6;
            a6 <= ($signed(x) * 8'd15) + a7;
            a7 <= ($signed(x) * 8'd17) + a8;
            a8 <= ($signed(x) * 8'd19) + a9;
            a9 <= ($signed(x) * 8'd19) + a10;
            a10 <= ($signed(x) * 8'd17) + a11;
            a11 <= ($signed(x) * 8'd15) + a12;
            a12 <= ($signed(x) * 8'd13) + a13;
            a13 <= ($signed(x) * 8'd11) + a14;
            a14 <= ($signed(x) * 8'd9) + a15;
            a15 <= ($signed(x) * 8'd7) + a16;
            a16 <= ($signed(x) * 8'd5) + a17;
            a17 <= ($signed(x) * 8'd3);
            y <= a0[15:0];
        end
    end
endmodule