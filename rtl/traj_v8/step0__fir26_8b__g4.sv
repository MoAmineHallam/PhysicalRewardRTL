module step0__fir26_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [23:0] acum;
    reg [7:0] samples [0:25];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 26; i = i + 1) samples[i] <= 8'd0;
            acum <= 24'd0;
            y <= 16'd0;
        end else begin
            samples[0] <= x;
            acum <= (3*samples[0]) + (5*samples[1]) + (7*samples[2]) + (9*samples[3]) + (11*samples[4]) + (13*samples[5]) + (15*samples[6]) + (17*samples[7]) + (19*samples[8]) + (21*samples[9]) + (23*samples[10]) + (25*samples[11]) + (27*samples[12]) + (27*samples[13]) + (25*samples[14]) + (23*samples[15]) + (21*samples[16]) + (19*samples[17]) + (17*samples[18]) + (15*samples[19]) + (13*samples[20]) + (11*samples[21]) + (9*samples[22]) + (7*samples[23]) + (5*samples[24]) + (3*samples[25]);
            for (i = 1; i < 26; i = i + 1) samples[i] <= samples[i-1];
            y <= acum[15:0];
        end
    end
endmodule