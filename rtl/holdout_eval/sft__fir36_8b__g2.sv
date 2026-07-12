module sft__fir36_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  delay0, delay1, delay2, delay3, delay4, delay5, delay6, delay7, delay8, delay9, delay10, delay11, delay12, delay13, delay14, delay15, delay16, delay17, delay18, delay19, delay20, delay21, delay22, delay23, delay24, delay25, delay26, delay27, delay28, delay29, delay30, delay31, delay32, delay33, delay34, delay35;
    wire [23:0] acc = 8'd3 * delay0 + 8'd5 * delay1 + 8'd7 * delay2 + 8'd9 * delay3 + 8'd11 * delay4 + 8'd13 * delay5 + 8'd15 * delay6 + 8'd17 * delay7 + 8'd19 * delay8 + 8'd21 * delay9 + 8'd23 * delay10 + 8'd25 * delay11 + 8'd27 * delay12 + 8'd29 * delay13 + 8'd31 * delay14 + 8'd33 * delay15 + 8'd35 * delay16 + 8'd37 * delay17 + 8'd37 * delay18 + 8'd35 * delay19 + 8'd33 * delay20 + 8'd31 * delay21 + 8'd29 * delay22 + 8'd27 * delay23 + 8'd25 * delay24 + 8'd23 * delay25 + 8'd21 * delay26 + 8'd19 * delay27 + 8'd17 * delay28 + 8'd15 * delay29 + 8'd13 * delay30 + 8'd11 * delay31 + 8'd9 * delay32 + 8'd7 * delay33 + 8'd5 * delay34 + 8'd3 * delay35;
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16'd0; delay0 <= 8'd0; delay1 <= 8'd0; delay2 <= 8'd0; delay3 <= 8'd0; delay4 <= 8'd0; delay5 <= 8'd0; delay6 <= 8'd0; delay7 <= 8'd0; delay8 <= 8'd0; delay9 <= 8'd0; delay10 <= 8'd0; delay11 <= 8'd0; delay12 <= 8'd0; delay13 <= 8'd0; delay14 <= 8'd0; delay15 <= 8'd0; delay16 <= 8'd0; delay17 <= 8'd0; delay18 <= 8'd0; delay19 <= 8'd0; delay20 <= 8'd0; delay21 <= 8'd0; delay22 <= 8'd0; delay23 <= 8'd0; delay24 <= 8'd0; delay25 <= 8'd0; delay26 <= 8'd0; delay27 <= 8'd0; delay28 <= 8'd0; delay29 <= 8'd0; delay30 <= 8'd0; delay31 <= 8'd0; delay32 <= 8'd0; delay33 <= 8'd0; delay34 <= 8'd0; delay35 <= 8'd0;
        end else begin
            y <= acc[15:0];
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
            delay29 <= delay28;
            delay30 <= delay29;
            delay31 <= delay30;
            delay32 <= delay31;
            delay33 <= delay32;
            delay34 <= delay33;
            delay35 <= delay34;
        end
    end
endmodule