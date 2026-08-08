module base__fir10_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [0:9];
integer i;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 0;
        for(i = 0; i < 10; i = i + 1) begin
            delay_line[i] <= 0;
        end
    end
    else begin
        delay_line[0] <= x;
        for(i = 0; i < 9; i = i + 1) begin
            delay_line[i+1] <= delay_line[i];
        end
        y <= (delay_line[0] * 3) + 
            (delay_line[1] * 5) + 
            (delay_line[2] * 7) + 
            (delay_line[3] * 9) + 
            (delay_line[4] * 11) + 
            (delay_line[5] * 11) + 
            (delay_line[6] * 9) + 
            (delay_line[7] * 7) + 
            (delay_line[8] * 5) + 
            (delay_line[9] * 3);
    end
end

endmodule