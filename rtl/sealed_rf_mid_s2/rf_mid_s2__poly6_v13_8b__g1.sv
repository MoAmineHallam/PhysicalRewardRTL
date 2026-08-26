module rf_mid_s2__poly6_v13_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [15:0] r1, r2, r3, r4, r5, r6, r7;
    reg [7:0] xd1, xd2, xd3, xd4, xd5, xd6;
    always @(posedge clk) begin
        if (!rst_n) begin r1 <= 16'd0; r2 <= 16'd0; r3 <= 16'd0; r4 <= 16'd0; r5 <= 16'd0; r6 <= 16'd0; r7 <= 16'd0; xd1 <= 8'd0; xd2 <= 8'd0; xd3 <= 8'd0; xd4 <= 8'd0; xd5 <= 8'd0; xd6 <= 8'd0; y <= 16'd0; end
        else begin
            r1 <= 16'd86;
            xd1 <= x;
            r2 <= r1 * xd1 + 16'd73;
            xd2 <= xd1;
            r3 <= r2 * xd2 + 16'd23;
            xd3 <= xd2;
            r4 <= r3 * xd3 + 16'd69;
            xd4 <= xd3;
            r5 <= r4 * xd4 + 16'd48;
            xd5 <= xd4;
            r6 <= r5 * xd5 + 16'd52;
            xd6 <= xd5;
            r7 <= r6 * xd6 + 16'd39;
            y <= r7;
        end
    end
endmodule
