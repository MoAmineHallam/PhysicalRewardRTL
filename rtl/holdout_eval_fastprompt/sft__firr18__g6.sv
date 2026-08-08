module sft__firr18__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:17];
    wire [15:0] acc = 16'd1 * xs[0] + 16'd2 * xs[1] + 16'd3 * xs[2] + 16'd4 * xs[3] + 16'd5 * xs[4] + 16'd6 * xs[5] + 16'd7 * xs[6] + 16'd8 * xs[7] + 16'd9 * xs[8] + 16'd10 * xs[9] + 16'd11 * xs[10] + 16'd12 * xs[11] + 16'd13 * xs[12] + 16'd14 * xs[13] + 16'd15 * xs[14] + 16'd16 * xs[15] + 16'd17 * xs[16] + 16'd18 * xs[17];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (int i = 0; i < 18; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (int i = 1; i < 18; i = i + 1) xs[i] <= xs[i-1];
            y <= acc;
        end
    end
endmodule