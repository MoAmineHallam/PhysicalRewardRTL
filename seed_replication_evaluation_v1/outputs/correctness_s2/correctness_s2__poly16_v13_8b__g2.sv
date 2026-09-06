module correctness_s2__poly16_v13_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire [15:0] t0 = 16'd45;
    wire [15:0] t1 = t0 * x + 16'd67;
    wire [15:0] t2 = t1 * x + 16'd56;
    wire [15:0] t3 = t2 * x + 16'd54;
    wire [15:0] t4 = t3 * x + 16'd26;
    wire [15:0] t5 = t4 * x + 16'd74;
    wire [15:0] t6 = t5 * x + 16'd47;
    wire [15:0] t7 = t6 * x + 16'd10;
    wire [15:0] t8 = t7 * x + 16'd96;
    wire [15:0] t9 = t8 * x + 16'd73;
    wire [15:0] t10 = t9 * x + 16'd22;
    wire [15:0] t11 = t10 * x + 16'd53;
    wire [15:0] t12 = t11 * x + 16'd23;
    wire [15:0] t13 = t12 * x + 16'd53;
    wire [15:0] t14 = t13 * x + 16'd77;
    wire [15:0] t15 = t14 * x + 16'd32;
    wire [15:0] t16 = t15 * x + 16'd61;
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= t16;
    end
endmodule
