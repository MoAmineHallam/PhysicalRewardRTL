module fir8_8b__g8 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] xd [0:7];
    reg [23:0] p [0:7];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 8; i = i + 1) begin xd[i] <= 8'd0; p[i] <= 24'd0; end
            y <= 16'd0;
        end else begin
            xd[0] <= x;
            for (i = 1; i < 8; i = i + 1) xd[i] <= xd[i-1];
            p[0] <= 8'd3 * xd[0];
            p[1] <= 8'd5 * xd[1];
            p[2] <= 8'd7 * xd[2];
            p[3] <= 8'd9 * xd[3];
            p[4] <= 8'd9 * xd[4];
            p[5] <= 8'd7 * xd[5];
            p[6] <= 8'd5 * xd[6];
            p[7] <= 8'd3 * xd[7];
            y <= p[0] + p[1] + p[2] + p[3] + p[4] + p[5] + p[6] + p[7];
        end
    end
endmodule