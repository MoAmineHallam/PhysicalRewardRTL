module sft__firr26__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  t0, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, t16, t17, t18, t19, t20, t21, t22, t23, t24, t25;
    wire [23:0] acc = 8'd1 * t0 + 8'd2 * t1 + 8'd3 * t2 + 8'd4 * t3 + 8'd5 * t4 + 8'd6 * t5 + 8'd7 * t6 + 8'd8 * t7 + 8'd9 * t8 + 8'd10 * t9 + 8'd11 * t10 + 8'd12 * t11 + 8'd13 * t12 + 8'd14 * t13 + 8'd15 * t14 + 8'd16 * t15 + 8'd17 * t16 + 8'd18 * t17 + 8'd19 * t18 + 8'd20 * t19 + 8'd21 * t20 + 8'd22 * t21 + 8'd23 * t22 + 8'd24 * t23 + 8'd25 * t24 + 8'd26 * t25;
    always @(posedge clk) begin
        if (!rst_n) begin
            t0 <= 8'd0; t1 <= 8'd0; t2 <= 8'd0; t3 <= 8'd0; t4 <= 8'd0; t5 <= 8'd0; t6 <= 8'd0; t7 <= 8'd0; t8 <= 8'd0; t9 <= 8'd0; t10 <= 8'd0; t11 <= 8'd0; t12 <= 8'd0; t13 <= 8'd0; t14 <= 8'd0; t15 <= 8'd0; t16 <= 8'd0; t17 <= 8'd0; t18 <= 8'd0; t19 <= 8'd0; t20 <= 8'd0; t21 <= 8'd0; t22 <= 8'd0; t23 <= 8'd0; t24 <= 8'd0; t25 <= 8'd0; y <= 16'd0;
        end else begin
            t0 <= x;
            t1 <= t0;
            t2 <= t1;
            t3 <= t2;
            t4 <= t3;
            t5 <= t4;
            t6 <= t5;
            t7 <= t6;
            t8 <= t7;
            t9 <= t8;
            t10 <= t9;
            t11 <= t10;
            t12 <= t11;
            t13 <= t12;
            t14 <= t13;
            t15 <= t14;
            t16 <= t15;
            t17 <= t16;
            t18 <= t17;
            t19 <= t18;
            t20 <= t19;
            t21 <= t20;
            t22 <= t21;
            t23 <= t22;
            t24 <= t23;
            t25 <= t24;
            y <= acc[15:0];
        end
    end
endmodule