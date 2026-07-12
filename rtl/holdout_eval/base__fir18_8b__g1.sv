module base__fir18_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] s [18:0];
reg [7:0] c [18:0];

assign c[0] = 3;
assign c[1] = 5;
assign c[2] = 7;
assign c[3] = 9;
assign c[4] = 11;
assign c[5] = 13;
assign c[6] = 15;
assign c[7] = 17;
assign c[8] = 19;
assign c[9] = 19;
assign c[10] = 17;
assign c[11] = 15;
assign c[12] = 13;
assign c[13] = 11;
assign c[14] = 9;
assign c[15] = 7;
assign c[16] = 5;
assign c[17] = 3;

integer i;

always @(posedge clk) begin
    if (!rst_n) begin
        for (i = 0; i < 18; i = i + 1) begin
            s[i] <= 0;
        end
        y <= 0;
    end
    else begin
        s[0] <= x;
        for (i = 1; i < 18; i = i + 1) begin
            s[i] <= s[i-1];
        end
        y <= s[17]*c[0] + s[16]*c[1] + s[15]*c[2] + s[14]*c[3] + s[13]*c[4] + s[12]*c[5] + s[11]*c[6] + s[10]*c[7] + s[9]*c[8] + s[8]*c[9] + s[7]*c[10] + s[6]*c[11] + s[5]*c[12] + s[4]*c[13] + s[3]*c[14] + s[2]*c[15] + s[1]*c[16] + s[0]*c[17];
    end
end

endmodule