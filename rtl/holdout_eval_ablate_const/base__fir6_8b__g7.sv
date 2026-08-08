module base__fir6_8b__g7 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [0:5];

integer i;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 6; i = i + 1) begin
            delay_line[i] <= 8'd0;
        end
        y <= 16'd0;
    end else begin
        for (i = 4; i >= 0; i = i - 1) begin
            delay_line[i+1] <= delay_line[i];
        end
        delay_line[0] <= x;
        y <= (delay_line[0] * 8'd3) + (delay_line[1] * 8'd5) + (delay_line[2] * 8'd7)
             + (delay_line[3] * 8'd7) + (delay_line[4] * 8'd5) + (delay_line[5] * 8'd3);
    end
end

endmodule