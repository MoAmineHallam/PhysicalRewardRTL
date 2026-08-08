module sft__firr6__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  l0, l1, l2, l3, l4, l5;
    wire [23:0] acc = 8'd1 * l0 + 8'd2 * l1 + 8'd3 * l2 + 8'd4 * l3 + 8'd5 * l4 + 8'd6 * l5;
    always @(posedge clk) begin
        if (!rst_n) begin
            l0 <= 8'd0; l1 <= 8'd0; l2 <= 8'd0; l3 <= 8'd0; l4 <= 8'd0; l5 <= 8'd0; y <= 16'd0;
        end else begin
            l0 <= x;
            l1 <= l0;
            l2 <= l1;
            l3 <= l2;
            l4 <= l3;
            l5 <= l4;
            y <= acc[15:0];
        end
    end
endmodule