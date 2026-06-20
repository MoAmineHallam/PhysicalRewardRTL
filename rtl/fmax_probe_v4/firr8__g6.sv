module firr8__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  s0, s1, s2, s3, s4, s5, s6, s7;
    wire [23:0] acc = 8'd1 * s0 + 8'd2 * s1 + 8'd3 * s2 + 8'd4 * s3 + 8'd5 * s4 + 8'd6 * s5 + 8'd7 * s6 + 8'd8 * s7;
    always @(posedge clk) begin
        if (!rst_n) begin
            s0 <= 8'd0; s1 <= 8'd0; s2 <= 8'd0; s3 <= 8'd0; s4 <= 8'd0; s5 <= 8'd0; s6 <= 8'd0; s7 <= 8'd0; y <= 16'd0;
        end else begin
            s0 <= x;
            s1 <= s0;
            s2 <= s1;
            s3 <= s2;
            s4 <= s3;
            s5 <= s4;
            s6 <= s5;
            s7 <= s6;
            y <= acc[15:0];
        end
    end
endmodule