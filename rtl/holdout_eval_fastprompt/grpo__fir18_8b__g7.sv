module grpo__fir18_8b__g7 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] delay0, delay1, delay2, delay3, delay4, delay5, delay6, delay7, delay8, delay9, delay10, delay11, delay12, delay13, delay14, delay15, delay16, delay17;
    reg [23:0] acc;
    always @(posedge clk) begin
        if (!rst_n) begin
            acc <= 24'd0;
            delay0 <= 8'd0; delay1 <= 8'd0; delay2 <= 8'd0; delay3 <= 8'd0; delay4 <= 8'd0; delay5 <= 8'd0; delay6 <= 8'd0; delay7 <= 8'd0; delay8 <= 8'd0; delay9 <= 8'd0; delay10 <= 8'd0; delay11 <= 8'd0; delay12 <= 8'd0; delay13 <= 8'd0; delay14 <= 8'd0; delay15 <= 8'd0; delay16 <= 8'd0; delay17 <= 8'd0;
            y <= 16'd0;
        end else begin
            acc <= delay0 * 8'd3 + delay1 * 8'd5 + delay2 * 8'd7 + delay3 * 8'd9 + delay4 * 8'd11 + delay5 * 8'd13 + delay6 * 8'd15 + delay7 * 8'd17 + delay8 * 8'd19 + delay9 * 8'd19 + delay10 * 8'd17 + delay11 * 8'd15 + delay12 * 8'd13 + delay13 * 8'd11 + delay14 * 8'd9 + delay15 * 8'd7 + delay16 * 8'd5 + delay17 * 8'd3;
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
            y <= acc[15:0];
        end
    end
endmodule