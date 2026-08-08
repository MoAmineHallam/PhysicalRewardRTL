module sft__poly7_v3_8b__g4 (
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
    always @(posedge clk) begin
        if (!rst_n) begin r0 <= 16'd0; r1 <= 16'd0; r2 <= 16'd0; r3 <= 16'd0; r4 <= 16'd0; r5 <= 16'd0; r6 <= 16'd0; r7 <= 16'd0; r8 <= 16'd0; y <= 16'd0; end
        else begin
            r0 <= 16'd85;
            r1 <= (16'd85 * x + 16'd16);
            r2 <= (16'd85 * x + 16'd16) * x + 16'd89;
            r3 <= ((16'd85 * x + 16'd16) * x + 16'd89) * x + 16'd64;
            r4 <= (((16'd85 * x + 16'd16) * x + 16'd89) * x + 16'd64) * x + 16'd12;
            r5 <= ((((16'd85 * x + 16'd16) * x + 16'd89) * x + 16'd64) * x + 16'd12) * x + 16'd36;
            r6 <= (((((16'd85 * x + 16'd16) * x + 16'd89) * x + 16'd64) * x + 16'd12) * x + 16'd36) * x + 16'd50;
            r7 <= ((((((16'd85 * x + 16'd16) * x + 16'd89) * x + 16'd64) * x + 16'd12) * x + 16'd36) * x + 16'd50) * x + 16'd90;
            r8 <= (((((((16'd85 * x + 16'd16) * x + 16'd89) * x + 16'd64) * x + 16'd12) * x + 16'd36) * x + 16'd50) * x + 16'd90) & 16'hFFFF;
            y <= r8;
        end
    end
endmodule