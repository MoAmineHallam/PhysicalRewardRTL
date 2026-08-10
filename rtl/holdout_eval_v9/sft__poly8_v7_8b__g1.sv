module sft__poly8_v7_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire [15:0] t0 = 16'd57;
    wire [15:0] t1 = t0 * x + 16'd11;
    wire [15:0] t2 = t1 * x + 16'd20;
    wire [15:0] t3 = t2 * x + 16'd96;
    wire [15:0] t4 = t3 * x + 16'd53;
    wire [15:0] t5 = t4 * x + 16'd74;
    wire [15:0] t6 = t5 * x + 16'd25;
    wire [15:0] t7 = t6 * x + 16'd52;
    wire [15:0] t8 = t7 * x + 16'd15;
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= t8;
    end
endmodule