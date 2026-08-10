module base__fir10_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

parameter COEF_A0 = 3;
parameter COEF_A1 = 5;
parameter COEF_A2 = 7;
parameter COEF_A3 = 9;
parameter COEF_A4 = 11;
parameter COEF_A5 = 11;
parameter COEF_A6 = 9;
parameter COEF_A7 = 7;
parameter COEF_A8 = 5;
parameter COEF_A9 = 3;

reg [7:0] x_delay [0:9]; // 10-element delay line for input samples

always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
        y <= 16'h0000; // clear output on reset
        for (int i = 0; i < 10; i = i + 1) begin
            x_delay[i] <= 8'h00; // clear delay line on reset
        end
    end
    else begin
        // shift input samples to delay line
        x_delay[0] <= x;
        for (int i = 1; i < 10; i = i + 1) begin
            x_delay[i] <= x_delay[i - 1];
        end

        // calculate output
        y <= (COEF_A0 * x_delay[0]) +
             (COEF_A1 * x_delay[1]) +
             (COEF_A2 * x_delay[2]) +
             (COEF_A3 * x_delay[3]) +
             (COEF_A4 * x_delay[4]) +
             (COEF_A5 * x_delay[5]) +
             (COEF_A6 * x_delay[6]) +
             (COEF_A7 * x_delay[7]) +
             (COEF_A8 * x_delay[8]) +
             (COEF_A9 * x_delay[9]);
    end
end

endmodule