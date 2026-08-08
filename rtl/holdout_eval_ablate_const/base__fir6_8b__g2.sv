module base__fir6_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] lfsr [5:0];
    wire [7:0] coeff [5:0];

    assign coeff[0] = 8'h03;
    assign coeff[1] = 8'h05;
    assign coeff[2] = 8'h07;
    assign coeff[3] = 8'h07;
    assign coeff[4] = 8'h05;
    assign coeff[5] = 8'h03;

    always @(posedge clk or negedge rst_n)
    begin
        if (~rst_n)
        begin
            y <= 16'd0;
            lfsr[0] <= 8'd0;
            lfsr[1] <= 8'd0;
            lfsr[2] <= 8'd0;
            lfsr[3] <= 8'd0;
            lfsr[4] <= 8'd0;
            lfsr[5] <= 8'd0;
        end
        else
        begin
            y <= lfsr[0]*coeff[0] + lfsr[1]*coeff[1] + lfsr[2]*coeff[2] + lfsr[3]*coeff[3] + lfsr[4]*coeff[4] + lfsr[5]*coeff[5];
            lfsr[0] <= x;
            lfsr[1] <= lfsr[0];
            lfsr[2] <= lfsr[1];
            lfsr[3] <= lfsr[2];
            lfsr[4] <= lfsr[3];
            lfsr[5] <= lfsr[4];
        end
    end
endmodule