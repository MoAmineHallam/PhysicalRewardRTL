module bestof8__poly7_v4_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire [15:0] t0 = 16'd20;
    wire [15:0] t1 = t0 * x + 16'd77;
    wire [15:0] t2 = t1 * x + 16'd15;
    wire [15:0] t3 = t2 * x + 16'd31;
    wire [15:0] t4 = t3 * x + 16'd25;
    wire [15:0] t5 = t4 * x + 16'd28;
    wire [15:0] t6 = t5 * x + 16'd45;
    wire [15:0] t7 = t6 * x + 16'd10;
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= t7;
    end
endmodule