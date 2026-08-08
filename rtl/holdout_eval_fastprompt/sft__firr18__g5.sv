module sft__firr18__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] xd [0:17];
    integer i;
    reg [23:0] acc;
    always @(*) acc = 8'd1 * xd[0] + 8'd2 * xd[1] + 8'd3 * xd[2] + 8'd4 * xd[3] + 8'd5 * xd[4] + 8'd6 * xd[5] + 8'd7 * xd[6] + 8'd8 * xd[7] + 8'd9 * xd[8] + 8'd10 * xd[9] + 8'd11 * xd[10] + 8'd12 * xd[11] + 8'd13 * xd[12] + 8'd14 * xd[13] + 8'd15 * xd[14] + 8'd16 * xd[15] + 8'd17 * xd[16] + 8'd18 * xd[17];
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1) xd[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xd[0] <= x;
            for (i = 1; i < 18; i = i + 1) xd[i] <= xd[i-1];
            y <= acc[15:0];
        end
    end
endmodule