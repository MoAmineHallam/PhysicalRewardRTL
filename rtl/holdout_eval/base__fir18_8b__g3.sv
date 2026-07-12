module base__fir18_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [0:17];
reg [15:0] coeff [0:17];

integer i;

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        y <= 0;
        for (i = 0; i < 18; i = i + 1) begin
            delay_line[i] <= 0;
        end
    end else begin
        y <= coeff[0]*delay_line[0] + coeff[1]*delay_line[1] + coeff[2]*delay_line[2] + coeff[3]*delay_line[3] + coeff[4]*delay_line[4] + coeff[5]*delay_line[5] + coeff[6]*delay_line[6] + coeff[7]*delay_line[7] + coeff[8]*delay_line[8] + coeff[9]*delay_line[9] + coeff[10]*delay_line[10] + coeff[11]*delay_line[11] + coeff[12]*delay_line[12] + coeff[13]*delay_line[13] + coeff[14]*delay_line[14] + coeff[15]*delay_line[15] + coeff[16]*delay_line[16] + coeff[17]*delay_line[17];
        for (i = 17; i > 0; i = i - 1) begin
            delay_line[i] <= delay_line[i-1];
        end
        delay_line[0] <= x;
    end
end

assign coeff[0] = 3;
assign coeff[1] = 5;
assign coeff[2] = 7;
assign coeff[3] = 9;
assign coeff[4] = 11;
assign coeff[5] = 13;
assign coeff[6] = 15;
assign coeff[7] = 17;
assign coeff[8] = 19;
assign coeff[9] = 19;
assign coeff[10] = 17;
assign coeff[11] = 15;
assign coeff[12] = 13;
assign coeff[13] = 11;
assign coeff[14] = 9;
assign coeff[15] = 7;
assign coeff[16] = 5;
assign coeff[17] = 3;

endmodule