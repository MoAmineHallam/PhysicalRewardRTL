module base__fir18_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delays [17:0];
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i=0; i<18; i=i+1) begin
                delays[i] <= 8'b0;
            end
            y <= 16'b0;
        end
        else begin
            // shift in the new sample and calculate output
            delays[0] <= x;
            for (i=1; i<18; i=i+1) begin
                delays[i] <= delays[i-1];
            end
            y <= delays[0]*3 + delays[1]*5 + delays[2]*7 + delays[3]*9 + delays[4]*11 + delays[5]*13 + delays[6]*15 + delays[7]*17 + delays[8]*19 + delays[9]*19 + delays[10]*17 + delays[11]*15 + delays[12]*13 + delays[13]*11 + delays[14]*9 + delays[15]*7 + delays[16]*5 + delays[17]*3;
        end
    end

endmodule