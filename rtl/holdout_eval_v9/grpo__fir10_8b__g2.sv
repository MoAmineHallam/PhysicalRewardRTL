module grpo__fir10_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] v0, v1, v2, v3, v4, v5, v6, v7, v8, v9;
    always @(posedge clk) begin
        if (!rst_n) begin
            v0 <= 24'd0; v1 <= 24'd0; v2 <= 24'd0; v3 <= 24'd0; v4 <= 24'd0; v5 <= 24'd0; v6 <= 24'd0; v7 <= 24'd0; v8 <= 24'd0; v9 <= 24'd0; y <= 16'd0;
        end else begin
            v0 <= 8'd3 * x + v1;
            v1 <= 8'd5 * x + v2;
            v2 <= 8'd7 * x + v3;
            v3 <= 8'd9 * x + v4;
            v4 <= 8'd11 * x + v5;
            v5 <= 8'd11 * x + v6;
            v6 <= 8'd9 * x + v7;
            v7 <= 8'd7 * x + v8;
            v8 <= 8'd5 * x + v9;
            v9 <= 8'd3 * x;
            y <= v0[15:0];
        end
    end
endmodule