module sft__firr10__g7 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] r0;
    reg [23:0] r1;
    reg [23:0] r2;
    reg [23:0] r3;
    reg [23:0] r4;
    reg [23:0] r5;
    reg [23:0] r6;
    reg [23:0] r7;
    reg [23:0] r8;
    reg [23:0] r9;
    always @(posedge clk) begin
        if (!rst_n) begin
            r0 <= 24'd0;
            r1 <= 24'd0;
            r2 <= 24'd0;
            r3 <= 24'd0;
            r4 <= 24'd0;
            r5 <= 24'd0;
            r6 <= 24'd0;
            r7 <= 24'd0;
            r8 <= 24'd0;
            r9 <= 24'd0;
        end else begin
            r0 <= 8'd1 * x + r1;
            r1 <= 8'd2 * x + r2;
            r2 <= 8'd3 * x + r3;
            r3 <= 8'd4 * x + r4;
            r4 <= 8'd5 * x + r5;
            r5 <= 8'd6 * x + r6;
            r6 <= 8'd7 * x + r7;
            r7 <= 8'd8 * x + r8;
            r8 <= 8'd9 * x + r9;
            r9 <= 8'd10 * x;
        end
    end
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= r0[15:0];
    end
endmodule