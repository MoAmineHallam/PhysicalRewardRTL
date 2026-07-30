module base__firr18__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:17];
    integer i;

    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
            for (i = 0; i < 18; i = i + 1) begin
                delay_line[i] <= 0;
            end
        end
        else begin
            y <= (1*delay_line[0] + 2*delay_line[1] + 3*delay_line[2] + 4*delay_line[3] + 5*delay_line[4] + 
                  6*delay_line[5] + 7*delay_line[6] + 8*delay_line[7] + 9*delay_line[8] + 10*delay_line[9] + 
                  11*delay_line[10] + 12*delay_line[11] + 13*delay_line[12] + 14*delay_line[13] + 15*delay_line[14] + 
                  16*delay_line[15] + 17*delay_line[16] + 18*delay_line[17]);

            delay_line[0] <= x;
            for (i = 1; i < 18; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
        end
    end

endmodule