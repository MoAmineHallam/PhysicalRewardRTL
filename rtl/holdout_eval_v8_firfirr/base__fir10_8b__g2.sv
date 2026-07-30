module base__fir10_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:9];
    reg [15:0] sum;
    
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1) begin
                delay_line[i] <= 8'h00;
            end
            sum <= 16'h0000;
            y <= 16'h0000;
        end else begin
            for (i = 9; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;
            sum <= 8'h03 * delay_line[0] + 8'h05 * delay_line[1] + 8'h07 * delay_line[2] + 8'h09 * delay_line[3] + 
                    8'h0B * delay_line[4] + 8'h0B * delay_line[5] + 8'h09 * delay_line[6] + 8'h07 * delay_line[7] + 
                    8'h05 * delay_line[8] + 8'h03 * delay_line[9];
            y <= sum;
        end
    end

endmodule