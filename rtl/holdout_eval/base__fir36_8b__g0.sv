module base__fir36_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:35]; // 36-element delay line
    integer i;

    always @(posedge clk) begin
        if(!rst_n) begin
            y <= 0;
            for(i=0; i<36; i=i+1) begin
                delay_line[i] <= 0;
            end
        end else begin
            y <= (delay_line[35]*3 + 
                delay_line[34]*5 + 
                delay_line[33]*7 + 
                delay_line[32]*9 + 
                delay_line[31]*11 + 
                delay_line[30]*13 + 
                delay_line[29]*15 + 
                delay_line[28]*17 + 
                delay_line[27]*19 + 
                delay_line[26]*21 + 
                delay_line[25]*23 + 
                delay_line[24]*25 + 
                delay_line[23]*27 + 
                delay_line[22]*29 + 
                delay_line[21]*31 + 
                delay_line[20]*33 + 
                delay_line[19]*35 + 
                delay_line[18]*37 + 
                delay_line[17]*37 + 
                delay_line[16]*35 + 
                delay_line[15]*33 + 
                delay_line[14]*31 + 
                delay_line[13]*29 + 
                delay_line[12]*27 + 
                delay_line[11]*25 + 
                delay_line[10]*23 + 
                delay_line[9]*21 + 
                delay_line[8]*19 + 
                delay_line[7]*17 + 
                delay_line[6]*15 + 
                delay_line[5]*13 + 
                delay_line[4]*11 + 
                delay_line[3]*9 + 
                delay_line[2]*7 + 
                delay_line[1]*5 + 
                delay_line[0]*3);
            
            // Shifting the delay_line
            for(i=35; i>0; i=i-1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;
        end
    end

endmodule