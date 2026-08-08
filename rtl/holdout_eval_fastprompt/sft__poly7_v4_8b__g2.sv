module sft__poly7_v4_8b__g2 (
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
    reg [15:0] y2;
    reg [15:0] x1;
    reg [15:0] x2;
    reg [15:0] x3;
    reg [15:0] x4;
    reg [15:0] x5;
    reg [15:0] x6;
    reg [15:0] x7;
    always @(posedge clk) begin
        if (!rst_n) begin r0 <= 16'd0; r1 <= 16'd0; r2 <= 16'd0; r3 <= 16'd0; r4 <= 16'd0; r5 <= 16'd0; r6 <= 16'd0; r7 <= 16'd0; y2 <= 16'd0; x1 <= 16'd0; x2 <= 16'd0; x3 <= 16'd0; x4 <= 16'd0; x5 <= 16'd0; x6 <= 16'd0; x7 <= 16'd0; y <= 16'd0; end
        else begin
            r0 <= 16'd20;
            x1 <= x;
            r1 <= r0 * x1 + 16'd77;
            x2 <= x1;
            r2 <= r1 * x2 + 16'd15;
            x3 <= x2;
            r3 <= r2 * x3 + 16'd31;
            x4 <= x3;
            r4 <= r3 * x4 + 16'd25;
            x5 <= x4;
            r5 <= r4 * x5 + 16'd28;
            x6 <= x5;
            r6 <= r5 * x6 + 16'd45;
            x7 <= x6;
            r7 <= r6 * x7 + 16'd10;
            y2 <= r7;
            y <= y2;
        end
    end
endmodule