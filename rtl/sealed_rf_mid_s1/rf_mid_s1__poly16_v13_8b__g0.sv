module rf_mid_s1__poly16_v13_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [15:0] r0, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15;
    reg [7:0] xd1, xd2, xd3, xd4, xd5, xd6, xd7, xd8, xd9, xd10, xd11, xd12, xd13, xd14, xd15, xd16;
    always @(posedge clk) begin
        if (!rst_n) begin r0 <= 16'd0; r1 <= 16'd0; r2 <= 16'd0; r3 <= 16'd0; r4 <= 16'd0; r5 <= 16'd0; r6 <= 16'd0; r7 <= 16'd0; r8 <= 16'd0; r9 <= 16'd0; r10 <= 16'd0; r11 <= 16'd0; r12 <= 16'd0; r13 <= 16'd0; r14 <= 16'd0; r15 <= 16'd0; end
        else begin
            r0 <= 16'd45;
            xd1 <= x; r1 <= r0 * xd1 + 16'd67;
            xd2 <= xd1; r2 <= r1 * xd2 + 16'd56;
            xd3 <= xd2; r3 <= r2 * xd3 + 16'd54;
            xd4 <= xd3; r4 <= r3 * xd4 + 16'd26;
            xd5 <= xd4; r5 <= r4 * xd5 + 16'd74;
            xd6 <= xd5; r6 <= r5 * xd6 + 16'd47;
            xd7 <= xd6; r7 <= r6 * xd7 + 16'd10;
            xd8 <= xd7; r8 <= r7 * xd8 + 16'd96;
            xd9 <= xd8; r9 <= r8 * xd9 + 16'd73;
            xd10 <= xd9; r10 <= r9 * xd10 + 16'd22;
            xd11 <= xd10; r11 <= r10 * xd11 + 16'd53;
            xd12 <= xd11; r12 <= r11 * xd12 + 16'd23;
            xd13 <= xd12; r13 <= r12 * xd13 + 16'd53;
            xd14 <= xd13; r14 <= r13 * xd14 + 16'd77;
            xd15 <= xd14; r15 <= r14 * xd15 + 16'd32;
            xd16 <= xd15; y <= r15 * xd16 + 16'd61;
        end
    end
endmodule
