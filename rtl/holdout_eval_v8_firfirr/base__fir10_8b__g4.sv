module base__fir10_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [0:9];
integer i;

always @(posedge clk) begin
    if (!rst_n) begin
        for (i = 0; i < 10; i = i + 1) begin
            delay_line[i] <= 8'd0;
        end
        y <= 16'd0;
    end else begin
        for (i = 0; i < 9; i = i +1) begin
            delay_line[i] <= delay_line[i+1];
        end
        delay_line[9] <= x;

        y <= (delay_line[0] * 8'd3) +
             (delay_line[1] * 8'd5) +
             (delay_line[2] * 8'd7) +
             (delay_line[3] * 8'd9) +
             (delay_line[4] * 8'd11) +
             (delay_line[5] * 8'd11) +
             (delay_line[6] * 8'd9) +
             (delay_line[7] * 8'd7) +
             (delay_line[8] * 8'd5) +
             (delay_line[9] * 8'd3);
    end
end

endmodule