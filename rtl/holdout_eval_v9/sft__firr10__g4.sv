module sft__firr10__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:9];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = xs[0] + 2*xs[1] + 3*xs[2] + 4*xs[3] + 5*xs[4] + 6*xs[5] + 7*xs[6] + 8*xs[7] + 9*xs[8] + 10*xs[9];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 10; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule