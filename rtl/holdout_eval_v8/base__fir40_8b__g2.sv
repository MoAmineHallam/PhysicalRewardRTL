module base__fir40_8b__g2 (
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
            delay_line[i] <= 8'd0;
        end
        y <= 16'd0;
    end else begin
        // Shift the delay line
        for (i = 39; i > 0; i = i - 1) begin
            delay_line[i] <= delay_line[i-1];
        end
        // Add the new sample to the delay line
        delay_line[0] <= x;
        // Generate the output
        y <= {{8{1'b0}}, delay_line[0]}*3 + {{6{1'b0}}, delay_line[1]}*5 + {{4{1'b0}}, delay_line[2]}*7 + {{2{1'b0}}, delay_line[3]}*9 + delay_line[4]*11 + delay_line[5]*13 + delay_line[6]*15 + delay_line[7]*17 + delay_line[8]*19 + delay_line[9]*21 + delay_line[10]*23 + delay_line[11]*25 + delay_line[12]*27 + delay_line[13]*29 + delay_line[14]*31 + delay_line[15]*33 + delay_line[16]*35 + delay_line[17]*37 + delay_line[18]*39 + delay_line[19]*41 + delay_line[20]*41 + delay_line[21]*39 + delay_line[22]*37 + delay_line[23]*35 + delay_line[24]*33 + delay_line[25]*31 + delay_line[26]*29 + delay_line[27]*27 + delay_line[28]*25 + delay_line[29]*23 + delay_line[30]*21 + delay_line[31]*19 + delay_line[32]*17 + delay_line[33]*15 + delay_line[34]*13 + delay_line[35]*11 + delay_line[36]*9 + delay_line[37]*7 + delay_line[38]*5 + delay_line[39]*3;
    end
end

endmodule