module correctness_s2__firr18_v5__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:17];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd0 +
        (2*8'd1 + 3)*xs[0] +
        (2*8'd2 + 3)*xs[1] +
        (2*8'd3 + 3)*xs[2] +
        (2*8'd4 + 3)*xs[3] +
        (2*8'd5 + 3)*xs[4] +
        (2*8'd6 + 3)*xs[5] +
        (2*8'd7 + 3)*xs[6] +
        (2*8'd8 + 3)*xs[7] +
        (2*8'd9 + 3)*xs[8] +
        (2*8'd10 + 3)*xs[9] +
        (2*8'd11 + 3)*xs[10] +
        (2*8'd12 + 3)*xs[11] +
        (2*8'd13 + 3)*xs[12] +
        (2*8'd14 + 3)*xs[13] +
        (2*8'd15 + 3)*xs[14] +
        (2*8'd16 + 3)*xs[15] +
        (2*8'd17 + 3)*xs[16] +
        (2*8'd18 + 3)*xs[17];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 18; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule
