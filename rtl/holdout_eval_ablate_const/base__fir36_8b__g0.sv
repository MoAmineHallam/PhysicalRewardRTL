module base__fir36_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] d_line [0:35]; // delay line
integer i;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 36; i = i + 1) begin
            d_line[i] <= 0;
        end
        y <= 0;
    end else begin
        // shift the delay line
        for (i = 0; i < 35; i = i + 1) begin
            d_line[i+1] <= d_line[i];
        end
        // insert new input sample
        d_line[0] <= x;
        // calculate output
        y <= {32'd0} +
             d_line[0]*3 +
             d_line[1]*5 +
             d_line[2]*7 +
             d_line[3]*9 +
             d_line[4]*11 +
             d_line[5]*13 +
             d_line[6]*15 +
             d_line[7]*17 +
             d_line[8]*19 +
             d_line[9]*21 +
             d_line[10]*23 +
             d_line[11]*25 +
             d_line[12]*27 +
             d_line[13]*29 +
             d_line[14]*31 +
             d_line[15]*33 +
             d_line[16]*35 +
             d_line[17]*37 +
             d_line[18]*37 +
             d_line[19]*35 +
             d_line[20]*33 +
             d_line[21]*31 +
             d_line[22]*29 +
             d_line[23]*27 +
             d_line[24]*25 +
             d_line[25]*23 +
             d_line[26]*21 +
             d_line[27]*19 +
             d_line[28]*17 +
             d_line[29]*15 +
             d_line[30]*13 +
             d_line[31]*11 +
             d_line[32]*9 +
             d_line[33]*7 +
             d_line[34]*5 +
             d_line[35]*3;
    end
end

endmodule