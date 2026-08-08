module base__fir6_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [5:0];
integer i;

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 6; i = i + 1) begin
            delay_line[i] <= 8'h00;
        end
        y <= 16'h0000;
    end
    else begin
        delay_line[0] <= x;
        for (i = 1; i < 6; i = i + 1) begin
            delay_line[i] <= delay_line[i-1];
        end
        y <= (delay_line[0] * 8'h03) + (delay_line[1] * 8'h05) + (delay_line[2] * 8'h07) +
             (delay_line[3] * 8'h07) + (delay_line[4] * 8'h05) + (delay_line[5] * 8'h03);
    end
end

endmodule