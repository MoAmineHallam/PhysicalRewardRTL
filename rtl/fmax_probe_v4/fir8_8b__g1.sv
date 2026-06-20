module fir8_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    // Tap values: [3, 5, 7, 9, 9, 7, 5, 3]
    localparam [7:0] tap0 = 8'd3, tap1 = 8'd5, tap2 = 8'd7, tap3 = 8'd9, tap4 = 8'd9, tap5 = 8'd7, tap6 = 8'd5, tap7 = 8'd3;
    reg [7:0] xs [0:7];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 8; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 8; i = i + 1) xs[i] <= xs[i-1];
            y <= {16{1'b0}} + tap0 * xs[0] + tap1 * xs[1] + tap2 * xs[2] + tap3 * xs[3] + tap4 * xs[4] + tap5 * xs[5] + tap6 * xs[6] + tap7 * xs[7];
        end
    end
endmodule