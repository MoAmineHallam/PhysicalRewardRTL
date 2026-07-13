module sft__firr6__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  t0;
    reg  [7:0]  t1;
    reg  [7:0]  t2;
    reg  [7:0]  t3;
    reg  [7:0]  t4;
    reg  [7:0]  t5;
    wire [23:0] acc = 8'd1 * t0 + 8'd2 * t1 + 8'd3 * t2 + 8'd4 * t3 + 8'd5 * t4 + 8'd6 * t5;
    always @(posedge clk) begin
        if (!rst_n) begin
            t0 <= 8'd0;
            t1 <= 8'd0;
            t2 <= 8'd0;
            t3 <= 8'd0;
            t4 <= 8'd0;
            t5 <= 8'd0;
            y <= 16'd0;
        end else begin
            t0 <= x;
            t1 <= t0;
            t2 <= t1;
            t3 <= t2;
            t4 <= t3;
            t5 <= t4;
            y <= acc[15:0];
        end
    end
endmodule