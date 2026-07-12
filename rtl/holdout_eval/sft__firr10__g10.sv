module sft__firr10__g10 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  s [0:9];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1) s[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            s[0] <= x;
            for (i = 1; i < 10; i = i + 1) s[i] <= s[i-1];
            y <= (8'd1 * s[0] + 8'd2 * s[1] + 8'd3 * s[2] + 8'd4 * s[3] + 8'd5 * s[4] + 8'd6 * s[5] + 8'd7 * s[6] + 8'd8 * s[7] + 8'd9 * s[8] + 8'd10 * s[9]);
        end
    end
endmodule