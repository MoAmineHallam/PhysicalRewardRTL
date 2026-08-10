module sft__fir10_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:9];
    reg  [15:0] prod [0:9];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1) begin xs[i] <= 8'd0; prod[i] <= 16'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 10; i = i + 1) xs[i] <= xs[i-1];
            prod[0] <= 8'd3 * xs[0];
            prod[1] <= 8'd5 * xs[1];
            prod[2] <= 8'd7 * xs[2];
            prod[3] <= 8'd9 * xs[3];
            prod[4] <= 8'd11 * xs[4];
            prod[5] <= 8'd11 * xs[5];
            prod[6] <= 8'd9 * xs[6];
            prod[7] <= 8'd7 * xs[7];
            prod[8] <= 8'd5 * xs[8];
            prod[9] <= 8'd3 * xs[9];
            y <= prod[0] + prod[1] + prod[2] + prod[3] + prod[4] + prod[5] + prod[6] + prod[7] + prod[8] + prod[9];
        end
    end
endmodule