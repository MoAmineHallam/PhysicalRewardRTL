module sft__firr26__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] p0, p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16, p17, p18, p19, p20, p21, p22, p23, p24, p25;
    always @(posedge clk) begin
        if (!rst_n) begin
            p0 <= 24'd0; p1 <= 24'd0; p2 <= 24'd0; p3 <= 24'd0; p4 <= 24'd0; p5 <= 24'd0; p6 <= 24'd0; p7 <= 24'd0; p8 <= 24'd0; p9 <= 24'd0; p10 <= 24'd0; p11 <= 24'd0; p12 <= 24'd0; p13 <= 24'd0; p14 <= 24'd0; p15 <= 24'd0; p16 <= 24'd0; p17 <= 24'd0; p18 <= 24'd0; p19 <= 24'd0; p20 <= 24'd0; p21 <= 24'd0; p22 <= 24'd0; p23 <= 24'd0; p24 <= 24'd0; p25 <= 24'd0; y <= 16'd0;
        end else begin
            p0 <= 8'd1 * x + p1;
            p1 <= 8'd2 * x + p2;
            p2 <= 8'd3 * x + p3;
            p3 <= 8'd4 * x + p4;
            p4 <= 8'd5 * x + p5;
            p5 <= 8'd6 * x + p6;
            p6 <= 8'd7 * x + p7;
            p7 <= 8'd8 * x + p8;
            p8 <= 8'd9 * x + p9;
            p9 <= 8'd10 * x + p10;
            p10 <= 8'd11 * x + p11;
            p11 <= 8'd12 * x + p12;
            p12 <= 8'd13 * x + p13;
            p13 <= 8'd14 * x + p14;
            p14 <= 8'd15 * x + p15;
            p15 <= 8'd16 * x + p16;
            p16 <= 8'd17 * x + p17;
            p17 <= 8'd18 * x + p18;
            p18 <= 8'd19 * x + p19;
            p19 <= 8'd20 * x + p20;
            p20 <= 8'd21 * x + p21;
            p21 <= 8'd22 * x + p22;
            p22 <= 8'd23 * x + p23;
            p23 <= 8'd24 * x + p24;
            p24 <= 8'd25 * x + p25;
            p25 <= 8'd26 * x;
            y <= p0[15:0];
        end
    end
endmodule