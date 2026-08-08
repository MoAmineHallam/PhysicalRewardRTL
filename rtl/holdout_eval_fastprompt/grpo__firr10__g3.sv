module grpo__firr10__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:9];
    reg  [15:0] y2;
    reg  [23:0] acc;
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
            y2 <= 16'd0;
            acc <= 24'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 10; i = i + 1) xs[i] <= xs[i-1];
            acc <= (1'd1 * xs[0]) + (2'd2 * xs[1]) + (3'd3 * xs[2]) + (4'd4 * xs[3]) + (5'd5 * xs[4]) + (6'd6 * xs[5]) + (7'd7 * xs[6]) + (8'd8 * xs[7]) + (9'd9 * xs[8]) + (10'd10 * xs[9]);
            y2 <= acc[15:0];
            y <= y2;
        end
    end
endmodule