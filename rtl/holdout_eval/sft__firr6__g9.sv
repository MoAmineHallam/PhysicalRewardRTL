module sft__firr6__g9 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] xd [0:5];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 6; i = i + 1) xd[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xd[0] <= x;
            for (i = 1; i < 6; i = i + 1) xd[i] <= xd[i-1];
            y <= 8'd1 * xd[0] + 8'd2 * xd[1] + 8'd3 * xd[2] + 8'd4 * xd[3] + 8'd5 * xd[4] + 8'd6 * xd[5];
        end
    end
endmodule