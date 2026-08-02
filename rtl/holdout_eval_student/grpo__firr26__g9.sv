module grpo__firr26__g9 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] r0, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15, r16, r17, r18, r19, r20, r21, r22, r23, r24, r25;
    always @(posedge clk) begin
        if (!rst_n) begin
            r0 <= 24'd0;
            r1 <= 24'd0;
            r2 <= 24'd0;
            r3 <= 24'd0;
            r4 <= 24'd0;
            r5 <= 24'd0;
            r6 <= 24'd0;
            r7 <= 24'd0;
            r8 <= 24'd0;
            r9 <= 24'd0;
            r10 <= 24'd0;
            r11 <= 24'd0;
            r12 <= 24'd0;
            r13 <= 24'd0;
            r14 <= 24'd0;
            r15 <= 24'd0;
            r16 <= 24'd0;
            r17 <= 24'd0;
            r18 <= 24'd0;
            r19 <= 24'd0;
            r20 <= 24'd0;
            r21 <= 24'd0;
            r22 <= 24'd0;
            r23 <= 24'd0;
            r24 <= 24'd0;
            r25 <= 24'd0;
            y <= 16'd0;
        end else begin
            r0 <= (8'd1 * x + r1) & 24'hFFFF;
            r1 <= (8'd2 * x + r2) & 24'hFFFF;
            r2 <= (8'd3 * x + r3) & 24'hFFFF;
            r3 <= (8'd4 * x + r4) & 24'hFFFF;
            r4 <= (8'd5 * x + r5) & 24'hFFFF;
            r5 <= (8'd6 * x + r6) & 24'hFFFF;
            r6 <= (8'd7 * x + r7) & 24'hFFFF;
            r7 <= (8'd8 * x + r8) & 24'hFFFF;
            r8 <= (8'd9 * x + r9) & 24'hFFFF;
            r9 <= (8'd10 * x + r10) & 24'hFFFF;
            r10 <= (8'd11 * x + r11) & 24'hFFFF;
            r11 <= (8'd12 * x + r12) & 24'hFFFF;
            r12 <= (8'd13 * x + r13) & 24'hFFFF;
            r13 <= (8'd14 * x + r14) & 24'hFFFF;
            r14 <= (8'd15 * x + r15) & 24'hFFFF;
            r15 <= (8'd16 * x + r16) & 24'hFFFF;
            r16 <= (8'd17 * x + r17) & 24'hFFFF;
            r17 <= (8'd18 * x + r18) & 24'hFFFF;
            r18 <= (8'd19 * x + r19) & 24'hFFFF;
            r19 <= (8'd20 * x + r20) & 24'hFFFF;
            r20 <= (8'd21 * x + r21) & 24'hFFFF;
            r21 <= (8'd22 * x + r22) & 24'hFFFF;
            r22 <= (8'd23 * x + r23) & 24'hFFFF;
            r23 <= (8'd24 * x + r24) & 24'hFFFF;
            r24 <= (8'd25 * x + r25) & 24'hFFFF;
            r25 <= (8'd26 * x) & 24'hFFFF;
            y <= r0[15:0];
        end
    end
endmodule