module base__fir18_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [0:17];
integer i;

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 18; i = i + 1) begin
            delay_line[i] <= 8'b0;
        end
        y <= 16'b0;
    end
    else begin
        delay_line[0] <= x;
        for (i = 1; i < 18; i = i + 1) begin
            delay_line[i] <= delay_line[i-1];
        end
        y <= delay_line[0]*3 + delay_line[1]*5 + delay_line[2]*7 + delay_line[3]*9 + delay_line[4]*11 + delay_line[5]*13 + delay_line[6]*15 + delay_line[7]*17 + delay_line[8]*19 + delay_line[9]*19 + delay_line[10]*17 + delay_line[11]*15 + delay_line[12]*13 + delay_line[13]*11 + delay_line[14]*9 + delay_line[15]*7 + delay_line[16]*5 + delay_line[17]*3;
    end
end

endmodule