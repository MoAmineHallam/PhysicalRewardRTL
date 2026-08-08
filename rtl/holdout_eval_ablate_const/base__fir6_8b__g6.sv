module base__fir6_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:5];
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'b0;
            for (i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 8'b0;
            end
        end else begin
            delay_line[0] <= x;
            y <= (delay_line[0] * 8'h03) + (delay_line[1] * 8'h05) + (delay_line[2] * 8'h07) + (delay_line[3] * 8'h07) + (delay_line[4] * 8'h05) + (delay_line[5] * 8'h03);
            for (i = 0; i < 5; i = i + 1) begin
                delay_line[i+1] <= delay_line[i];
            end
        end
    end

endmodule