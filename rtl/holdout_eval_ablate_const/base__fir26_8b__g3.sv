module base__fir26_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:25];
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 26; i = i + 1) begin
                delay_line[i] <= 8'b0;
            end
            y <= 16'b0;
        end else begin
            delay_line[0] <= x;
            for (i = 1; i < 26; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
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
                 {8'b0, delay_line[13]} * 27 +
                 {8'b0, delay_line[14]} * 25 +
                 {8'b0, delay_line[15]} * 23 +
                 {8'b0, delay_line[16]} * 21 +
                 {8'b0, delay_line[17]} * 19 +
                 {8'b0, delay_line[18]} * 17 +
                 {8'b0, delay_line[19]} * 15 +
                 {8'b0, delay_line[20]} * 13 +
                 {8'b0, delay_line[21]} * 11 +
                 {8'b0, delay_line[22]} * 9 +
                 {8'b0, delay_line[23]} * 7 +
                 {8'b0, delay_line[24]} * 5 +
                 {8'b0, delay_line[25]} * 3;
        end
    end
endmodule