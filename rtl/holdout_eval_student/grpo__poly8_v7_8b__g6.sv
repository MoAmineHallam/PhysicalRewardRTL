module grpo__poly8_v7_8b__g6 (
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
    wire [15:0] y_reg = r8;
    reg [7:0] xd1;
    reg [7:0] xd2;
    reg [7:0] xd3;
    reg [7:0] xd4;
    reg [7:0] xd5;
    reg [7:0] xd6;
    reg [7:0] xd7;
    reg [7:0] xd8;
    always @(posedge clk) begin
        if (!rst_n) begin
            r0 <= 16'd57;
            r1 <= 16'd0;
            r2 <= 16'd0;
            r3 <= 16'd0;
            r4 <= 16'd0;
            r5 <= 16'd0;
            r6 <= 16'd0;
            r7 <= 16'd0;
            r8 <= 16'd0;
            xd1 <= 8'd0;
            xd2 <= 8'd0;
            xd3 <= 8'd0;
            xd4 <= 8'd0;
            xd5 <= 8'd0;
            xd6 <= 8'd0;
            xd7 <= 8'd0;
            xd8 <= 8'd0;
        end else begin
            r0 <= 16'd57;
            r1 <= r0 * xd1 + 16'd11;
            r2 <= r1 * xd2 + 16'd20;
            r3 <= r2 * xd3 + 16'd96;
            r4 <= r3 * xd4 + 16'd53;
            r5 <= r4 * xd5 + 16'd74;
            r6 <= r5 * xd6 + 16'd25;
            r7 <= r6 * xd7 + 16'd52;
            r8 <= r7 * xd8 + 16'd15;
            xd1 <= x;
            xd2 <= xd1;
            xd3 <= xd2;
            xd4 <= xd3;
            xd5 <= xd4;
            xd6 <= xd5;
            xd7 <= xd6;
            xd8 <= xd7;
        end
    end
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= y_reg;
    end
endmodule