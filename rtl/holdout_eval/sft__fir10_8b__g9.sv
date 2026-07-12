module sft__fir10_8b__g9 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xd [0:9];
    wire [23:0] acc = 8'd3 * xd[0] + 8'd5 * xd[1] + 8'd7 * xd[2] + 8'd9 * xd[3] + 8'd11 * xd[4] + 8'd11 * xd[5] + 8'd9 * xd[6] + 8'd7 * xd[7] + 8'd5 * xd[8] + 8'd3 * xd[9];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (int i = 0; i < 10; i = i + 1) xd[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xd[0] <= x;
            for (int i = 1; i < 10; i = i + 1) xd[i] <= xd[i-1];
            y <= acc[15:0];
        end
    end
endmodule