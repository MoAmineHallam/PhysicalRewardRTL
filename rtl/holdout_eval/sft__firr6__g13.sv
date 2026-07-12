module sft__firr6__g13 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] xs [0:5];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 6; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 6; i = i + 1) xs[i] <= xs[i-1];
            y <= (8'd1 * xs[0]) + (8'd2 * xs[1]) + (8'd3 * xs[2]) + (8'd4 * xs[3]) + (8'd5 * xs[4]) + (8'd6 * xs[5]);
        end
    end
endmodule