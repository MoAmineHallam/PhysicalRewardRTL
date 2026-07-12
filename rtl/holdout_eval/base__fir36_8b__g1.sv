module base__fir36_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

parameter tap = 36;

reg [7:0] delay [0:tap-1]; // 36-point delay of past sample.

integer i;

always @(posedge clk) begin
    if (!rst_n) begin
        y <= 0;
        for (i = 0; i < tap; i = i + 1)
            delay[i] <= 0;
    end else begin
        delay[0] <= x; // input sample stored in first place in delay line
        delay[1] <= delay[0]; // shift in previous sample 
        delay[tap-1] <= delay[tap-2]; // shift in previous sample
        // Perform multiplication and addition in order to obtain output
        y <= (delay[0]*3)+(delay[1]*5)+(delay[2]*7)+(delay[3]*9)+(delay[4]*11)+(delay[5]*13)+
             (delay[6]*15)+(delay[7]*17)+(delay[8]*19)+(delay[9]*21)+(delay[10]*23)+(delay[11]*25)+
             (delay[12]*27)+(delay[13]*29)+(delay[14]*31)+(delay[15]*33)+(delay[16]*35)+(delay[17]*37)+
             (delay[18]*37)+(delay[19]*35)+(delay[20]*33)+(delay[21]*31)+(delay[22]*29)+(delay[23]*27)+
             (delay[24]*25)+(delay[25]*23)+(delay[26]*21)+(delay[27]*19)+(delay[28]*17)+(delay[29]*15)+
             (delay[30]*13)+(delay[31]*11)+(delay[32]*9)+(delay[33]*7)+(delay[34]*5)+(delay[35]*3); 
        // Shift everything left in the delay line
        for (i = tap-1; i > 0; i = i - 1)
            delay[i] <= delay[i-1];
    end
end

endmodule