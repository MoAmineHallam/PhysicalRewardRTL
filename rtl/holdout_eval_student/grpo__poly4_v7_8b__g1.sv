module grpo__poly4_v7_8b__g1 (
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
    reg [7:0] xd1;
    reg [7:0] xd2;
    reg [7:0] xd3;
    reg [7:0] xd4;
    always @(posedge clk) begin
        if (!rst_n) begin
            r0 <= 16'd0;
            r1 <= 16'd0;
            r2 <= 16'd0;
            r3 <= 16'd0;
            r4 <= 16'd0;
            xd1 <= 8'd0;
            xd2 <= 8'd0;
            xd3 <= 8'd0;
            xd4 <= 8'd0;
        end else begin
            r0 <= 16'd24;
            xd1 <= x;
            r1 <= r0 * xd1 + 16'd36;
            xd2 <= xd1;
            r2 <= r1 * xd2 + 16'd17;
            xd3 <= xd2;
            r3 <= r2 * xd3 + 16'd21;
            xd4 <= xd3;
            r4 <= r3 * xd4 + 16'd50;
        end
    end
    always @(posedge clk) y <= r4;
endmodule