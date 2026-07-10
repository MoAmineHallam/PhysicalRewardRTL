module sft__poly6_8b__g2 (
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
    wire [15:0] p0 = r0;
    wire [15:0] p1 = p0 * x + 16'd3;
    wire [15:0] p2 = p1 * x + 16'd5;
    wire [15:0] p3 = p2 * x + 16'd7;
    wire [15:0] p4 = p3 * x + 16'd9;
    wire [15:0] p5 = p4 * x + 16'd11;
    wire [15:0] p6 = p5 * x + 16'd13;
    always @(posedge clk) begin
        if (!rst_n) begin r0 <= 16'd0; r1 <= 16'd0; r2 <= 16'd0; r3 <= 16'd0; r4 <= 16'd0; r5 <= 16'd0; r6 <= 16'd0; y <= 16'd0; end
        else begin
            r0 <= 16'd1;
            r1 <= p1;
            r2 <= p2;
            r3 <= p3;
            r4 <= p4;
            r5 <= p5;
            r6 <= p6;
            y <= r6;
        end
    end
endmodule