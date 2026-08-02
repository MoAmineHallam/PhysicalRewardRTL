module sft__firr6__g9 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0, a1, a2, a3, a4, a5;
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16'd0;
            a0 <= 24'd0;
            a1 <= 24'd0;
            a2 <= 24'd0;
            a3 <= 24'd0;
            a4 <= 24'd0;
            a5 <= 24'd0;
        end else begin
            y <= {a5[15:0], a4[15:0], a3[15:0], a2[15:0], a1[15:0], a0[15:0]};
            a0 <= (8'd1) * x + a1;
            a1 <= (8'd2) * x + a2;
            a2 <= (8'd3) * x + a3;
            a3 <= (8'd4) * x + a4;
            a4 <= (8'd5) * x + a5;
            a5 <= (8'd6) * x;
        end
    end
endmodule