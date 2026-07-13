module grpo__firr10__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a;
    reg [7:0] xs [0:9];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            a <= 24'd0;
            for (i = 0; i < 10; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            a <= 24'd0 + 24'd1 * xs[0] + 24'd2 * xs[1] + 24'd3 * xs[2] + 24'd4 * xs[3] + 24'd5 * xs[4] + 24'd6 * xs[5] + 24'd7 * xs[6] + 24'd8 * xs[7] + 24'd9 * xs[8] + 24'd10 * xs[9];
            y <= a[15:0];
            xs[0] <= x;
            for (i = 1; i < 10; i = i + 1) xs[i] <= xs[i-1];
        end
    end
endmodule