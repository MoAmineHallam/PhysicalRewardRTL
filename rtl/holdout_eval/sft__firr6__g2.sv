module sft__firr6__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:5];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 6; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 6; i = i + 1) xs[i] <= xs[i-1];
            y <= 16'd1 * xs[0] + 16'd2 * xs[1] + 16'd3 * xs[2] + 16'd4 * xs[3] + 16'd5 * xs[4] + 16'd6 * xs[5];
        end
    end
endmodule