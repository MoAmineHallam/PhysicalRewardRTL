module sft__firr6__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  r0, r1, r2, r3, r4, r5;
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = 8'd1 * r0 + 8'd2 * r1 + 8'd3 * r2 + 8'd4 * r3 + 8'd5 * r4 + 8'd6 * r5;
    always @(posedge clk) begin
        if (!rst_n) begin
            r0 <= 8'd0; r1 <= 8'd0; r2 <= 8'd0; r3 <= 8'd0; r4 <= 8'd0; r5 <= 8'd0; y <= 16'd0;
        end else begin
            r0 <= x;
            r1 <= r0;
            r2 <= r1;
            r3 <= r2;
            r4 <= r3;
            r5 <= r4;
            y <= acc[15:0];
        end
    end
endmodule