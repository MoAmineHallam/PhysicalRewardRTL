module firr4__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:3];
    reg  [15:0] p  [0:3];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 4; i = 1 + i) begin xs[i] <= 8'd0; p[i] <= 16'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 4; i = 1 + i) xs[i] <= xs[i-1];
            p[0] <= 8'd1 * xs[0];
            p[1] <= 8'd2 * xs[1];
            p[2] <= 8'd3 * xs[2];
            p[3] <= 8'd4 * xs[3];
            y <= p[0] + p[1] + p[2] + p[3];
        end
    end
endmodule