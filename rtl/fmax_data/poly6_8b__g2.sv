module poly6_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire [15:0] t0 = 16'd1;
    wire [15:0] t1 = t0 * x + 16'd3;
    wire [15:0] t2 = t1 * x + 16'd5;
    wire [15:0] t3 = t2 * x + 16'd7;
    wire [15:0] t4 = t3 * x + 16'd9;
    wire [15:0] t5 = t4 * x + 16'd11;
    wire [15:0] t6 = t5 * x + 16'd13;
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= t6;
    end
endmodule