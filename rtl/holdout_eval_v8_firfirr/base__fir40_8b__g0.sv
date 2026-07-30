module base__fir40_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:39];
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1) begin
                delay_line[i] <= 8'b0;
            end
            y <= 16'b0;
        end
        else begin
            for (i = 39; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;
            
            y <= {8'b0, delay_line[0]} * 3 +
                 {8'b0, delay_line[1]} * 5 +
                 {8'b0, delay_line[2]} * 7 +
                 {8'b0, delay_line[3]} * 9 +
                 {8'b0, delay_line[4]} * 11 +
                 {8'b0, delay_line[5]} * 13 +
                 {8'b0, delay_line[6]} * 15 +
                 {8'b0, delay_line[7]} * 17 +
                 {8'b0, delay_line[8]} * 19 +
                 {8'b0, delay_line[9]} * 21 +
                 {8'b0, delay_line[10]} * 23 +
                 {8'b0, delay_line[11]} * 25 +
                 {8'b0, delay_line[12]} * 27 +
                 {8'b0, delay_line[13]} * 29 +
                 {8'b0, delay_line[14]} * 31 +
                 {8'b0, delay_line[15]} * 33 +
                 {8'b0, delay_line[16]} * 35 +
                 {8'b0, delay_line[17]} * 37 +
                 {8'b0, delay_line[18]} * 39 +
                 {8'b0, delay_line[19]} * 41 +
                 {8'b0, delay_line[20]} * 41 +
                 {8'b0, delay_line[21]} * 39 +
                 {8'b0, delay_line[22]} * 37 +
                 {8'b0, delay_line[23]} * 35 +
                 {8'b0, delay_line[24]} * 33 +
                 {8'b0, delay_line[25]} * 31 +
                 {8'b0, delay_line[26]} * 29 +
                 {8'b0, delay_line[27]} * 27 +
                 {8'b0, delay_line[28]} * 25 +
                 {8'b0, delay_line[29]} * 23 +
                 {8'b0, delay_line[30]} * 21 +
                 {8'b0, delay_line[31]} * 19 +
                 {8'b0, delay_line[32]} * 17 +
                 {8'b0, delay_line[33]} * 15 +
                 {8'b0, delay_line[34]} * 13 +
                 {8'b0, delay_line[35]} * 11 +
                 {8'b0, delay_line[36]} * 9 +
                 {8'b0, delay_line[37]} * 7 +
                 {8'b0, delay_line[38]} * 5 +
                 {8'b0, delay_line[39]} * 3;
        end
    end

endmodule