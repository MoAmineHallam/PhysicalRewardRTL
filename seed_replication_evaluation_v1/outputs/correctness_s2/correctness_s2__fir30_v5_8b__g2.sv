module correctness_s2__fir30_v5_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire [23:0] acc = 44*x + 37*delay0 + 25*delay1 + 24*delay2 + 58*delay3 + 4*delay4 + 24*delay5 + 58*delay6 + 23*delay7 + 46*delay8 + 25*delay9 + 35*delay10 + 40*delay11 + 8*delay12 + 33*delay13 + 12*delay14 + 18*delay15 + 9*delay16 + 63*delay17 + 4*delay18 + 1*delay19 + 45*delay20 + 21*delay21 + 43*delay22 + 25*delay23 + 33*delay24 + 4*delay25 + 57*delay26 + 44*delay27 + 11*delay28;
    reg  [7:0]  delay0, delay1, delay2, delay3, delay4, delay5, delay6, delay7, delay8, delay9, delay10, delay11, delay12, delay13, delay14, delay15, delay16, delay17, delay18, delay19, delay20, delay21, delay22, delay23, delay24, delay25, delay26, delay27, delay28;
    always @(posedge clk) begin
        if (!rst_n) begin
            delay0 <= 8'd0; delay1 <= 8'd0; delay2 <= 8'd0; delay3 <= 8'd0; delay4 <= 8'd0; delay5 <= 8'd0; delay6 <= 8'd0; delay7 <= 8'd0; delay8 <= 8'd0; delay9 <= 8'd0; delay10 <= 8'd0; delay11 <= 8'd0; delay12 <= 8'd0; delay13 <= 8'd0; delay14 <= 8'd0; delay15 <= 8'd0; delay16 <= 8'd0; delay17 <= 8'd0; delay18 <= 8'd0; delay19 <= 8'd0; delay20 <= 8'd0; delay21 <= 8'd0; delay22 <= 8'd0; delay23 <= 8'd0; delay24 <= 8'd0; delay25 <= 8'd0; delay26 <= 8'd0; delay27 <= 8'd0; delay28 <= 8'd0; y <= 16'd0;
        end else begin
            delay0 <= x;
            delay1 <= delay0;
            delay2 <= delay1;
            delay3 <= delay2;
            delay4 <= delay3;
            delay5 <= delay4;
            delay6 <= delay5;
            delay7 <= delay6;
            delay8 <= delay7;
            delay9 <= delay8;
            delay10 <= delay9;
            delay11 <= delay10;
            delay12 <= delay11;
            delay13 <= delay12;
            delay14 <= delay13;
            delay15 <= delay14;
            delay16 <= delay15;
            delay17 <= delay16;
            delay18 <= delay17;
            delay19 <= delay18;
            delay20 <= delay19;
            delay21 <= delay20;
            delay22 <= delay21;
            delay23 <= delay22;
            delay24 <= delay23;
            delay25 <= delay24;
            delay26 <= delay25;
            delay27 <= delay26;
            delay28 <= delay27;
            y <= acc[15:0];
        end
    end
endmodule
