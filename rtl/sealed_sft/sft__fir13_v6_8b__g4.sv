module sft__fir13_v6_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:12];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 24'd19 * xs[0] + 24'd28 * xs[1] + 24'd42 * xs[2] + 24'd41 * xs[3] + 24'd60 * xs[4] + 24'd8 * xs[5] + 24'd17 * xs[6] + 24'd9 * xs[7] + 24'd28 * xs[8] + 24'd42 * xs[9] + 24'd19 * xs[10] + 24'd44 * xs[11] + 24'd37 * xs[12];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 13; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 13; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule
