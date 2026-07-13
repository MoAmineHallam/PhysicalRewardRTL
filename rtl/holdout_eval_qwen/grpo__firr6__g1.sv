module grpo__firr6__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0;
    reg [23:0] a1;
    reg [23:0] a2;
    reg [23:0] a3;
    reg [23:0] a4;
    reg [23:0] a5;
    reg [7:0] xs [0:5];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= 24'd0;
            a1 <= 24'd0;
            a2 <= 24'd0;
            a3 <= 24'd0;
            a4 <= 24'd0;
            a5 <= 24'd0;
            for (i = 0; i < 6; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            a0 <= 8'd1 * xs[0] + 8'd2 * xs[1] + 8'd3 * xs[2] + 8'd4 * xs[3] + 8'd5 * xs[4] + 8'd6 * xs[5];
            xs[0] <= x;
            xs[1] <= xs[0];
            xs[2] <= xs[1];
            xs[3] <= xs[2];
            xs[4] <= xs[3];
            xs[5] <= xs[4];
            y <= a0[15:0];
        end
    end
endmodule