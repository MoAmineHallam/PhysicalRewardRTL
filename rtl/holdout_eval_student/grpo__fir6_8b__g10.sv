module grpo__fir6_8b__g10 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] acc;
    reg [7:0] xd1;
    reg [7:0] xd2;
    reg [7:0] xd3;
    reg [7:0] xd4;
    reg [7:0] xd5;
    reg [7:0] xd6;
    always @(posedge clk) begin
        if (!rst_n) begin
            acc <= 24'd0;
            xd1 <= 8'd0;
            xd2 <= 8'd0;
            xd3 <= 8'd0;
            xd4 <= 8'd0;
            xd5 <= 8'd0;
            xd6 <= 8'd0;
            y <= 16'd0;
        end else begin
            acc <= 24'd3 * xd1 + 24'd5 * xd2 + 24'd7 * xd3 + 24'd7 * xd4 + 24'd5 * xd5 + 24'd3 * xd6;
            y <= acc[15:0];
            xd6 <= xd5;
            xd5 <= xd4;
            xd4 <= xd3;
            xd3 <= xd2;
            xd2 <= xd1;
            xd1 <= x;
        end
    end
endmodule