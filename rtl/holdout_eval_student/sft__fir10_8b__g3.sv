module sft__fir10_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] r0, r1, r2, r3, r4, r5, r6, r7, r8, r9;
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
            y <= 16'd0;
        end else begin
            r0 <= ((24'd3 * x) + r1) & 24'hFFFF;
            r1 <= ((24'd5 * x) + r2) & 24'hFFFF;
            r2 <= ((24'd7 * x) + r3) & 24'hFFFF;
            r3 <= ((24'd9 * x) + r4) & 24'hFFFF;
            r4 <= ((24'd11 * x) + r5) & 24'hFFFF;
            r5 <= ((24'd11 * x) + r6) & 24'hFFFF;
            r6 <= ((24'd9 * x) + r7) & 24'hFFFF;
            r7 <= ((24'd7 * x) + r8) & 24'hFFFF;
            r8 <= ((24'd5 * x) + r9) & 24'hFFFF;
            r9 <= ((24'd3 * x) + 24'd0) & 24'hFFFF;
            y <= r0[15:0];
        end
    end
endmodule