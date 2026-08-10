module s400__fir6_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] acc = 24'd0;
    reg [7:0] xs [0:5];
    always @(posedge clk) begin
        if (!rst_n) begin
            acc <= 24'd0;
            for (int i = 0; i < 6; i = i + 1) xs[i] <= 8'd0;
        end else begin
            acc <= (24'd3 * xs[0]) + (24'd5 * xs[1]) + (24'd7 * xs[2]) + (24'd7 * xs[3]) + (24'd5 * xs[4]) + (24'd3 * xs[5]);
            for (int i = 0; i < 5; i = i + 1) xs[i] <= xs[i+1];
            xs[5] <= x;
        end
    end
    always @(posedge clk) begin
        y <= acc[15:0];
    end
endmodule