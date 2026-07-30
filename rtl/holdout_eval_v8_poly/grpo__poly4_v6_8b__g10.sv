module grpo__poly4_v6_8b__g10 (
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
    wire [15:0] y_reg = r4;
    reg [7:0] xd1;
    reg [7:0] xd2;
    reg [7:0] xd3;
    reg [7:0] xd4;
    always @(posedge clk) begin
        if (!rst_n) begin
            r0 <= 16'd65;
            r1 <= 16'd0;
            r2 <= 16'd0;
            r3 <= 16'd0;
            r4 <= 16'd0;
            xd1 <= 8'd0;
            xd2 <= 8'd0;
            xd3 <= 8'd0;
            xd4 <= 8'd0;
        end else begin
            r0 <= 16'd65;
            r1 <= r0 * xd1 + 16'd29;
            r2 <= r1 * xd2 + 16'd88;
            r3 <= r2 * xd3 + 16'd44;
            r4 <= r3 * xd4 + 16'd17;
            xd1 <= x;
            xd2 <= xd1;
            xd3 <= xd2;
            xd4 <= xd3;
        end
    end
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= y_reg;
    end
endmodule