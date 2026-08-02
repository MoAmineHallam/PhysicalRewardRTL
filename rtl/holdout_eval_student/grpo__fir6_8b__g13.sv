module grpo__fir6_8b__g13 (
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
    always @(posedge clk) begin
        if (!rst_n) begin
            r1 <= 16'd0;
            r2 <= 16'd0;
            r3 <= 16'd0;
            r4 <= 16'd0;
            r5 <= 16'd0;
            r6 <= 16'd0;
            y <= 16'd0;
        end else begin
            r1 <= 8'd3 * x + r2;
            r2 <= 8'd5 * x + r3;
            r3 <= 8'd7 * x + r4;
            r4 <= 8'd7 * x + r5;
            r5 <= 8'd5 * x + r6;
            r6 <= 8'd3 * x;
            y <= r1[15:0];
        end
    end
endmodule