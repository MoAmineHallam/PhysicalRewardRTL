module fir8_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [15:0] r1;
    reg [15:0] r2;
    reg [15:0] r3;
    reg [15:0] r4;
    reg [15:0] r5;
    reg [15:0] r6;
    reg [15:0] r7;
    reg [15:0] r8;
    wire [23:0] acc = 8'd3 * r1 + 8'd5 * r2 + 8'd7 * r3 + 8'd9 * r4 + 8'd9 * r5 + 8'd7 * r6 + 8'd5 * r7 + 8'd3 * r8;
    always @(posedge clk) begin
        if (!rst_n) begin
            r1 <= 16'd0;
            r2 <= 16'd0;
            r3 <= 16'd0;
            r4 <= 16'd0;
            r5 <= 16'd0;
            r6 <= 16'd0;
            r7 <= 16'd0;
            r8 <= 16'd0;
            y <= 16'd0;
        end else begin
            r1 <= x;
            r2 <= r1;
            r3 <= r2;
            r4 <= r3;
            r5 <= r4;
            r6 <= r5;
            r7 <= r6;
            r8 <= r7;
            y <= acc[15:0];
        end
    end
endmodule