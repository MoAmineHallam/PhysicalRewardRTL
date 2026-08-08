module base__fir10_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // declare delays
    reg [7:0] delay_0;
    reg [7:0] delay_1;
    reg [7:0] delay_2;
    reg [7:0] delay_3;
    reg [7:0] delay_4;
    reg [7:0] delay_5;
    reg [7:0] delay_6;
    reg [7:0] delay_7;
    reg [7:0] delay_8;
    reg [7:0] delay_9;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin // reset
            delay_0 <= 8'd0;
            delay_1 <= 8'd0;
            delay_2 <= 8'd0;
            delay_3 <= 8'd0;
            delay_4 <= 8'd0;
            delay_5 <= 8'd0;
            delay_6 <= 8'd0;
            delay_7 <= 8'd0;
            delay_8 <= 8'd0;
            delay_9 <= 8'd0;
            y <= 16'd0;
        end
        else begin // non-reset
            delay_0 <= x;
            delay_1 <= delay_0;
            delay_2 <= delay_1;
            delay_3 <= delay_2;
            delay_4 <= delay_3;
            delay_5 <= delay_4;
            delay_6 <= delay_5;
            delay_7 <= delay_6;
            delay_8 <= delay_7;
            delay_9 <= delay_8;

            y <= (3 * delay_0) + (5 * delay_1) + (7 * delay_2) + (9 * delay_3) + (11 * delay_4) + (11 * delay_5) + (9 * delay_6) + (7 * delay_7) + (5 * delay_8) + (3 * delay_9);
        end
    end
endmodule