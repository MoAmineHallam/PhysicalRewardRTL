module s100__firr6__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] a0, a1, a2, a3, a4, a5;
    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= '0; a1 <= '0; a2 <= '0; a3 <= '0; a4 <= '0; a5 <= '0; y <= '0;
        end else begin
            a0 <= 8'd1 * x + a1;
            a1 <= 8'd2 * x + a2;
            a2 <= 8'd3 * x + a3;
            a3 <= 8'd4 * x + a4;
            a4 <= 8'd5 * x + a5;
            a5 <= 8'd6 * x;
            y <= a0[15:0];
        end
    end
endmodule