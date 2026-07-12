module sft__firr6__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] x0, x1, x2, x3, x4, x5;
    reg [23:0] acc;
    always @(posedge clk) begin
        if (!rst_n) begin
            x0 <= 8'd0; x1 <= 8'd0; x2 <= 8'd0; x3 <= 8'd0; x4 <= 8'd0; x5 <= 8'd0; acc <= 24'd0; y <= 16'd0;
        end else begin
            x0 <= x;
            x1 <= x0;
            x2 <= x1;
            x3 <= x2;
            x4 <= x3;
            x5 <= x4;
            acc <= 8'd1 * x0 + 8'd2 * x1 + 8'd3 * x2 + 8'd4 * x3 + 8'd5 * x4 + 8'd6 * x5;
            y <= acc[15:0];
        end
    end
endmodule