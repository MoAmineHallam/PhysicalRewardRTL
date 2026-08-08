module grpo__fir6_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:5];
    wire [15:0] acc = 8'd3 * xs[0] + 8'd5 * xs[1] + 8'd7 * xs[2] + 8'd7 * xs[3] + 8'd5 * xs[4] + 8'd3 * xs[5];
    always @(posedge clk) begin
        if (!rst_n) begin
            foreach (xs[i]) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (int i = 1; i < 6; i++) xs[i] <= xs[i-1];
            y <= acc;
        end
    end
endmodule