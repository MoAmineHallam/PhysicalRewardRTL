module base__fir40_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] shift_reg [0:39];
integer i;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 0;
        for (i = 0; i < 40; i = i + 1) begin
            shift_reg[i] <= 0;
        end
    end
    else begin
        // Shift in new sample
        shift_reg[0] <= x;
        for (i = 1; i < 40; i = i + 1) begin
            shift_reg[i] <= shift_reg[i-1];
        end

        // Compute output
        y <= 
            (shift_reg[0]*3) + 
            (shift_reg[1]*5) + 
            (shift_reg[2]*7) + 
            (shift_reg[3]*9) + 
            (shift_reg[4]*11) +
            (shift_reg[5]*13) +
            (shift_reg[6]*15) +
            (shift_reg[7]*17) +
            (shift_reg[8]*19) +
            (shift_reg[9]*21) +
            (shift_reg[10]*23) +
            (shift_reg[11]*25) +
            (shift_reg[12]*27) +
            (shift_reg[13]*29) +
            (shift_reg[14]*31) +
            (shift_reg[15]*33) +
            (shift_reg[16]*35) +
            (shift_reg[17]*37) +
            (shift_reg[18]*39) +
            (shift_reg[19]*41) +
            (shift_reg[20]*41) +
            (shift_reg[21]*39) +
            (shift_reg[22]*37) +
            (shift_reg[23]*35) +
            (shift_reg[24]*33) +
            (shift_reg[25]*31) +
            (shift_reg[26]*29) +
            (shift_reg[27]*27) +
            (shift_reg[28]*25) +
            (shift_reg[29]*23) +
            (shift_reg[30]*21) +
            (shift_reg[31]*19) +
            (shift_reg[32]*17) +
            (shift_reg[33]*15) +
            (shift_reg[34]*13) +
            (shift_reg[35]*11) +
            (shift_reg[36]*9) +
            (shift_reg[37]*7) +
            (shift_reg[38]*5) +
            (shift_reg[39]*3);
    end
end

endmodule