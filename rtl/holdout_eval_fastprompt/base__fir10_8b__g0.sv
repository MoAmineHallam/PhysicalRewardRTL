module base__fir10_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line[10];
    reg [15:0] sum;
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (rst_n == 0) begin
            y <= 0;
            sum <= 0;
            for (i = 0; i < 10; i = i + 1) begin
                delay_line[i] <= 0;
            end
        end else begin
            // Update delay line
            delay_line[0] <= x;
            for (i = 1; i < 10; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            // Calculate sum of products of taps with coefficients
            sum <= (delay_line[0] * 3) + 
                   (delay_line[1] * 5) + 
                   (delay_line[2] * 7) + 
                   (delay_line[3] * 9) + 
                   (delay_line[4] * 11) + 
                   (delay_line[5] * 11) +
                   (delay_line[6] * 9) + 
                   (delay_line[7] * 7) + 
                   (delay_line[8] * 5) + 
                   (delay_line[9] * 3);
            // Pipeline output
            y <= sum[15:0];
        end
    end
endmodule