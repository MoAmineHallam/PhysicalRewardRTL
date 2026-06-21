module fir4_8b__g9 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:3];
    reg  [23:0] acc;
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 4; i = i + 1) xs[i] <= 8'd0;
            acc <= 24'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 4; i = i + 1) xs[i] <= xs[i-1];
            acc <= 8'd3 * xs[0] + 8'd5 * xs[1] + 8'd5 * xs[2] + 8'd3 * xs[3];
            y <= acc[15:0];
        end
    end
endmodule