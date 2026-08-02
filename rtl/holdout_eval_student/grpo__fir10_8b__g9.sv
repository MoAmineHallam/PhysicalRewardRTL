module grpo__fir10_8b__g9 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] r1;
    reg [23:0] r2;
    reg [23:0] r3;
    reg [23:0] r4;
    reg [23:0] r5;
    reg [23:0] r6;
    reg [23:0] r7;
    reg [23:0] r8;
    reg [23:0] r9;
    reg [23:0] r10;
    always @(posedge clk) begin
        if (!rst_n) begin
            r1 <= 24'd0;
            r2 <= 24'd0;
            r3 <= 24'd0;
            r4 <= 24'd0;
            r5 <= 24'd0;
            r6 <= 24'd0;
            r7 <= 24'd0;
            r8 <= 24'd0;
            r9 <= 24'd0;
            r10 <= 24'd0;
            y <= 16'd0;
        end else begin
            r1 <= 8'd3 * x + r2;
            r2 <= 8'd5 * x + r3;
            r3 <= 8'd7 * x + r4;
            r4 <= 8'd9 * x + r5;
            r5 <= 8'd11 * x + r6;
            r6 <= 8'd11 * x + r7;
            r7 <= 8'd9 * x + r8;
            r8 <= 8'd7 * x + r9;
            r9 <= 8'd5 * x + r10;
            r10 <= 8'd3 * x;
            y <= r1[15:0];
        end
    end
endmodule