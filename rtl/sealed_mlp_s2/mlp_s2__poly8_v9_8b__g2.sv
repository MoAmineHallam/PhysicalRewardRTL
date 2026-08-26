module mlp_s2__poly8_v9_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [15:0] r0;
    reg [15:0] r1;
    reg [15:0] r2;
    reg [15:0] r3;
    reg [15:0] r4;
    reg [15:0] r5;
    reg [15:0] r6;
    reg [15:0] r7;
    reg [15:0] r8;
    reg [7:0] x_d1;
    reg [7:0] x_d2;
    reg [7:0] x_d3;
    reg [7:0] x_d4;
    reg [7:0] x_d5;
    reg [7:0] x_d6;
    reg [7:0] x_d7;
    reg [7:0] x_d8;
    always @(posedge clk) begin
        if (!rst_n) begin
            r0 <= 16'd0;
            r1 <= 16'd0;
            r2 <= 16'd0;
            r3 <= 16'd0;
            r4 <= 16'd0;
            r5 <= 16'd0;
            r6 <= 16'd0;
            r7 <= 16'd0;
            r8 <= 16'd0;
            x_d1 <= 8'd0;
            x_d2 <= 8'd0;
            x_d3 <= 8'd0;
            x_d4 <= 8'd0;
            x_d5 <= 8'd0;
            x_d6 <= 8'd0;
            x_d7 <= 8'd0;
            x_d8 <= 8'd0;
        end else begin
            r0 <= 16'd65;
            r1 <= r0 * x_d1 + 16'd30;
            r2 <= r1 * x_d2 + 16'd3;
            r3 <= r2 * x_d3 + 16'd97;
            r4 <= r3 * x_d4 + 16'd7;
            r5 <= r4 * x_d5 + 16'd99;
            r6 <= r5 * x_d6 + 16'd95;
            r7 <= r6 * x_d7 + 16'd42;
            r8 <= r7 * x_d8 + 16'd1;
            x_d1 <= x;
            x_d2 <= x_d1;
            x_d3 <= x_d2;
            x_d4 <= x_d3;
            x_d5 <= x_d4;
            x_d6 <= x_d5;
            x_d7 <= x_d6;
            x_d8 <= x_d7;
        end
    end
    assign y = r8;
endmodule
