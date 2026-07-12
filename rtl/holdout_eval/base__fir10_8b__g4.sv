module base__fir10_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line[9:0];
reg [15:0] accumulator;

integer i;

always @(posedge clk) begin
    if (!rst_n) begin
        y <= 0;
        accumulator <= 0;
        for (i=0; i<10; i=i+1) begin
            delay_line[i] <= 0;
        end
    end else begin
        delay_line[0] <= x;
        for (i=0; i<9; i=i+1) begin
            delay_line[i+1] <= delay_line[i];
        end
        accumulator <= delay_line[0]*(3+0) + delay_line[1]*(5+0) + delay_line[2]*(7+0) + delay_line[3]*(9+0) + delay_line[4]*(11+0) + delay_line[5]*(11+0) + delay_line[6]*(9+0) + delay_line[7]*(7+0) + delay_line[8]*(5+0) + delay_line[9]*(3+0);
        y <= accumulator;
    end
end

endmodule