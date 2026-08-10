module base__fir18_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] samples[0:17];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < 18; i = i + 1) begin
                samples[i] <= 8'b0;
            end
            y <= 16'b0;
        end else begin
            // push x into samples[0]
            samples[0] <= x;
            // compute new y
            y <= (samples[0]*3 + samples[1]*5 + samples[2]*7 + samples[3]*9 + samples[4]*11 + samples[5]*13 + samples[6]*15 + samples[7]*17 + samples[8]*19 + samples[9]*19 + samples[10]*17 + samples[11]*15 + samples[12]*13 + samples[13]*11 + samples[14]*9 + samples[15]*7 + samples[16]*5 + samples[17]*3);
            // shift samples
            for (int i = 17; i >= 1; i = i - 1) begin
                samples[i] <= samples[i-1];
            end
        end
    end

endmodule