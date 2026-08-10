module sft__firr6__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] p0, p1, p2, p3, p4, p5;
    always @(posedge clk) begin
        if (!rst_n) begin
            p0 <= 24'd0; p1 <= 24'd0; p2 <= 24'd0; p3 <= 24'd0; p4 <= 24'd0; p5 <= 24'd0; y <= 16'd0;
        end else begin
            p0 <= 8'd1 * x + p1;
            p1 <= 8'd2 * x + p2;
            p2 <= 8'd3 * x + p3;
            p3 <= 8'd4 * x + p4;
            p4 <= 8'd5 * x + p5;
            p5 <= 8'd6 * x;
            y <= p0[15:0];
        end
    end
endmodule