module grpo__firr6__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:5];
    reg  [15:0] y2;
    wire [23:0] acc = 8'd1 * xs[0] + 8'd2 * xs[1] + 8'd3 * xs[2] + 8'd4 * xs[3] + 8'd5 * xs[4] + 8'd6 * xs[5];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (int i = 0; i < 6; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0; y2 <= 16'd0;
        end else begin
            xs[0] <= x;
            for (int i = 1; i < 6; i = i + 1) xs[i] <= xs[i-1];
            y2 <= acc[15:0];
            y <= y2;
        end
    end
endmodule