module grpo__fir6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [15:0] r0, r1, r2, r3, r4, r5;
    wire [23:0] p0 = 8'd3 * x;
    wire [23:0] p1 = 8'd5 * r0;
    wire [23:0] p2 = 8'd7 * r1;
    wire [23:0] p3 = 8'd7 * r2;
    wire [23:0] p4 = 8'd5 * r3;
    wire [23:0] p5 = 8'd3 * r4;
    always @(posedge clk) begin
        if (!rst_n) begin
            r0 <= 16'd0;
            r1 <= 16'd0;
            r2 <= 16'd0;
            r3 <= 16'd0;
            r4 <= 16'd0;
            r5 <= 16'd0;
            y <= 16'd0;
        end else begin
            r0 <= x;
            r1 <= r0;
            r2 <= r1;
            r3 <= r2;
            r4 <= r3;
            r5 <= r4;
            y <= p0[15:0] + p1[15:0] + p2[15:0] + p3[15:0] + p4[15:0] + p5[15:0];
        end
    end
endmodule