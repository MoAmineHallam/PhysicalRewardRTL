module base__fir10_8b__g2 (
    input wire clk,
    input wire rst_n,
    input wire [7:0] x,
    output reg [15:0] y
);

reg [7:0] delay_line [0:9];
reg [15:0] acc;
reg [3:0] i;

always @(posedge clk) begin
    if (!rst_n) begin
        y <= 0;
        acc <= 0;
        for (i = 0; i < 10; i = i + 1) begin
            delay_line[i] <= 0;
        end
    end else begin
        y <= acc;
        acc <= x * 3 + delay_line[0] * 5 + delay_line[1] * 7 + delay_line[2] * 9 + delay_line[3] * 11 +
              delay_line[4] * 11 + delay_line[5] * 9 + delay_line[6] * 7 + delay_line[7] * 5 + delay_line[8] * 3;

        for (i = 9; i > 0; i = i - 1) begin
            delay_line[i] <= delay_line[i - 1];
        end
        delay_line[0] <= x;
    end
end

endmodule