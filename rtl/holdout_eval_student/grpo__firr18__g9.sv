module grpo__firr18__g9 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] r0, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15, r16, r17;
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
            y <= 16'd0;
        end else begin
            r0 <= 8'd1 * x + r1;
            r1 <= 8'd2 * x + r2;
            r2 <= 8'd3 * x + r3;
            r3 <= 8'd4 * x + r4;
            r4 <= 8'd5 * x + r5;
            r5 <= 8'd6 * x + r6;
            r6 <= 8'd7 * x + r7;
            r7 <= 8'd8 * x + r8;
            r8 <= 8'd9 * x + r9;
            r9 <= 8'd10 * x + r10;
            r10 <= 8'd11 * x + r11;
            r11 <= 8'd12 * x + r12;
            r12 <= 8'd13 * x + r13;
            r13 <= 8'd14 * x + r14;
            r14 <= 8'd15 * x + r15;
            r15 <= 8'd16 * x + r16;
            r16 <= 8'd17 * x + r17;
            r17 <= 8'd18 * x;
            y <= r0[15:0];
        end
    end
endmodule