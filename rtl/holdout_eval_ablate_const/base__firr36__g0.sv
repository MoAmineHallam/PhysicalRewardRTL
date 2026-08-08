module base__firr36__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap [0:35];
    integer i;
    
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 36; i = i + 1) begin
                tap[i] <= 0;
            end
            y <= 0;
        end
        else begin
            tap[0] <= x;
            for (i = 1; i < 36; i = i + 1) begin
                tap[i] <= tap[i-1];
            end
            y <= (1*tap[0]) + (2*tap[1]) + (3*tap[2]) + (4*tap[3]) + (5*tap[4]) + (6*tap[5]) + (7*tap[6]) + (8*tap[7]) + (9*tap[8]) + (10*tap[9]) + (11*tap[10]) + (12*tap[11]) + (13*tap[12]) + (14*tap[13]) + (15*tap[14]) + (16*tap[15]) + (17*tap[16]) + (18*tap[17]) + (19*tap[18]) + (20*tap[19]) + (21*tap[20]) + (22*tap[21]) + (23*tap[22]) + (24*tap[23]) + (25*tap[24]) + (26*tap[25]) + (27*tap[26]) + (28*tap[27]) + (29*tap[28]) + (30*tap[29]) + (31*tap[30]) + (32*tap[31]) + (33*tap[32]) + (34*tap[33]) + (35*tap[34]) + (36*tap[35]);
        end
    end
    
endmodule