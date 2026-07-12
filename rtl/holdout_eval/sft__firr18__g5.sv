module sft__firr18__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] samples [0:17];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1) samples[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            samples[0] <= x;
            for (i = 1; i < 18; i = i + 1) samples[i] <= samples[i-1];
            y <= 8'd1 * samples[0] + 8'd2 * samples[1] + 8'd3 * samples[2] + 8'd4 * samples[3] + 8'd5 * samples[4] + 8'd6 * samples[5] + 8'd7 * samples[6] + 8'd8 * samples[7] + 8'd9 * samples[8] + 8'd10 * samples[9] + 8'd11 * samples[10] + 8'd12 * samples[11] + 8'd13 * samples[12] + 8'd14 * samples[13] + 8'd15 * samples[14] + 8'd16 * samples[15] + 8'd17 * samples[16] + 8'd18 * samples[17];
        end
    end
endmodule