module base__fir10_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [9:0];
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1) begin
                delay_line[i] <= 8'b0;
            end
            y <= 16'b0;
        end else begin
            for (i = 9; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;
            
            y <= (delay_line[0] * 3) + (delay_line[1] * 5) +
                 (delay_line[2] * 7) + (delay_line[3] * 9) +
                 (delay_line[4] * 11) + (delay_line[5] * 11) +
                 (delay_line[6] * 9) + (delay_line[7] * 7) +
                 (delay_line[8] * 5) + (delay_line[9] * 3);
        end
    end
    
endmodule