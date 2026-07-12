module sft__fir26_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] mem [0:25];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 26; i = i + 1) mem[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            mem[0] <= x;
            for (i = 1; i < 26; i = i + 1) mem[i] <= mem[i-1];
            y <= mem[0]*8'd3 + mem[1]*8'd5 + mem[2]*8'd7 + mem[3]*8'd9 + mem[4]*8'd11 + mem[5]*8'd13 + mem[6]*8'd15 + mem[7]*8'd17 + mem[8]*8'd19 + mem[9]*8'd21 + mem[10]*8'd23 + mem[11]*8'd25 + mem[12]*8'd27 + mem[13]*8'd27 + mem[14]*8'd25 + mem[15]*8'd23 + mem[16]*8'd21 + mem[17]*8'd19 + mem[18]*8'd17 + mem[19]*8'd15 + mem[20]*8'd13 + mem[21]*8'd11 + mem[22]*8'd9 + mem[23]*8'd7 + mem[24]*8'd5 + mem[25]*8'd3;
        end
    end
endmodule