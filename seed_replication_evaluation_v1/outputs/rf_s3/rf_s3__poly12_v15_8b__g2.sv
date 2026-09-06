module rf_s3__poly12_v15_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [15:0] r0, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12;
    reg  [7:0] d0, d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12;
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= r12;
        r0 <= 16'd48;
        d0 <= x;
        r1 <= r0 * d0 + 16'd24;
        d1 <= d0;
        r2 <= r1 * d1 + 16'd79;
        d2 <= d1;
        r3 <= r2 * d2 + 16'd2;
        d3 <= d2;
        r4 <= r3 * d3 + 16'd46;
        d4 <= d3;
        r5 <= r4 * d4 + 16'd35;
        d5 <= d4;
        r6 <= r5 * d5 + 16'd44;
        d6 <= d5;
        r7 <= r6 * d6 + 16'd66;
        d7 <= d6;
        r8 <= r7 * d7 + 16'd80;
        d8 <= d7;
        r9 <= r8 * d8 + 16'd64;
        d9 <= d8;
        r10 <= r9 * d9 + 16'd18;
        d10 <= d9;
        r11 <= r10 * d10 + 16'd58;
        d11 <= d10;
        r12 <= r11 * d11 + 16'd51;
        d12 <= d11;
    end
endmodule
