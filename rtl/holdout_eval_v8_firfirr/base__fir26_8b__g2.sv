module base__fir26_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] dline [0:25];
    integer i;

    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
            for (i = 0; i < 26; i = i + 1) begin
                dline[i] <= 0;
            end
        end else begin
            // shift in new sample
            dline[0] <= x;
            // generate output by summing product of taps and delayed samples
            y <= (dline[0]*3) + (dline[1]*5) + (dline[2]*7) + (dline[3]*9) + (dline[4]*11) + (dline[5]*13) + (dline[6]*15) + (dline[7]*17) + (dline[8]*19) + (dline[9]*21) + (dline[10]*23) + (dline[11]*25) + (dline[12]*27) + (dline[13]*27) + (dline[14]*25) + (dline[15]*23) + (dline[16]*21) + (dline[17]*19) + (dline[18]*17) + (dline[19]*15) + (dline[20]*13) + (dline[21]*11) + (dline[22]*9) + (dline[23]*7) + (dline[24]*5) + (dline[25]*3);
            // shift delayed samples
            for (i = 25; i > 0; i = i - 1) begin
                dline[i] <= dline[i-1];
            end
        end
    end

endmodule