module sft__poly7_v1_8b__g6 (
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
    always @(*) r0 = 16;
    always @(*) r1 = r0 * x + 91;
    always @(*) r2 = r1 * x + 42;
    always @(*) r3 = r2 * x + 85;
    always @(*) r4 = r3 * x + 48;
    always @(*) r5 = r4 * x + 89;
    always @(*) r6 = r5 * x + 88;
    always @(*) r7 = r6 * x + 18;
    always @(*) r8 = r7;
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16;
            r0 <= 16;
            r1 <= 91;
            r2 <= 42;
            r3 <= 85;
            r4 <= 48;
            r5 <= 89;
            r6 <= 88;
            r7 <= 18;
            r8 <= 0;
        end else begin
            y <= r8;
            r0 <= 16;
            r1 <= r0 * x + 91;
            r2 <= r1 * x + 42;
            r3 <= r2 * x + 85;
            r4 <= r3 * x + 48;
            r5 <= r4 * x + 89;
            r6 <= r5 * x + 88;
            r7 <= r6 * x + 18;
            r8 <= r7;
        end
    end
endmodule