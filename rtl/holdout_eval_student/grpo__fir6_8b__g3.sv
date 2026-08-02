module grpo__fir6_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] q0;
    reg [23:0] q1;
    reg [23:0] q2;
    reg [23:0] q3;
    reg [23:0] q4;
    reg [23:0] q5;
    always @(posedge clk) begin
        if (!rst_n) begin
            q0 <= 24'd0;
            q1 <= 24'd0;
            q2 <= 24'd0;
            q3 <= 24'd0;
            q4 <= 24'd0;
            q5 <= 24'd0;
            y <= 16'd0;
        end else begin
            q0 <= 8'd3 * x + q1;
            q1 <= 8'd5 * x + q2;
            q2 <= 8'd7 * x + q3;
            q3 <= 8'd7 * x + q4;
            q4 <= 8'd5 * x + q5;
            q5 <= 8'd3 * x;
            y <= q0[15:0];
        end
    end
endmodule