module sft__fir8_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  s [0:7];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd3 * s[0] + 8'd5 * s[1] + 8'd7 * s[2] + 8'd9 * s[3] + 8'd9 * s[4] + 8'd7 * s[5] + 8'd5 * s[6] + 8'd3 * s[7];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 8; i = i + 1) s[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            s[0] <= x;
            for (i = 1; i < 8; i = i + 1) s[i] <= s[i-1];
            y <= acc[15:0];
        end
    end
endmodule