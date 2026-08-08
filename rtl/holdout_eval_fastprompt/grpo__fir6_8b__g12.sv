module grpo__fir6_8b__g12 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:5];
    reg  [15:0] ys [0:5];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (int i = 0; i < 6; i++) begin xs[i] <= 8'd0; ys[i] <= 16'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (int i = 1; i < 6; i++) xs[i] <= xs[i-1];
            ys[0] <= 8'd3 * xs[0] + 8'd5 * xs[1] + 8'd7 * xs[2] + 8'd7 * xs[3] + 8'd5 * xs[4] + 8'd3 * xs[5];
            for (int i = 1; i < 6; i++) ys[i] <= ys[i-1];
            y <= ys[5];
        end
    end
endmodule