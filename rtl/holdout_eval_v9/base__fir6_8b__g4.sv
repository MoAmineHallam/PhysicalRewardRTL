module base__fir6_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [5:0];

integer i;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 16'b0;
        for (i = 0; i < 6; i = i + 1) begin
            delay_line[i] <= 8'b0;
        end
    end else begin
        y <= x * 3 + delay_line[0] * 5 + delay_line[1] * 7 + delay_line[2] * 7 + delay_line[3] * 5 + delay_line[4] * 3;
        for (i = 4; i >= 1; i = i - 1) begin
            delay_line[i] <= delay_line[i-1];
        end
        delay_line[0] <= x;
    end
end

endmodule