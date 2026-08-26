module rf_mid_s1__poly12_v15_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire [15:0] t0 = 16'd48;
    wire [15:0] t1 = t0 * x + 16'd24;
    wire [15:0] t2 = t1 * x + 16'd79;
    wire [15:0] t3 = t2 * x + 16'd2;
    wire [15:0] t4 = t3 * x + 16'd46;
    wire [15:0] t5 = t4 * x + 16'd35;
    wire [15:0] t6 = t5 * x + 16'd44;
    wire [15:0] t7 = t6 * x + 16'd66;
    wire [15:0] t8 = t7 * x + 16'd80;
    wire [15:0] t9 = t8 * x + 16'd64;
    wire [15:0] t10 = t9 * x + 16'd18;
    wire [15:0] t11 = t10 * x + 16'd58;
    wire [15:0] t12 = t11 * x + 16'd51;
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= t12;
    end
endmodule
