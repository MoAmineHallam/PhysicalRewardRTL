module base__fir6_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_0, delay_1, delay_2, delay_3, delay_4, delay_5;
    reg [15:0] accu;
    parameter COEFF_0 = 3;
    parameter COEFF_1 = 5;
    parameter COEFF_2 = 7;
    parameter COEFF_3 = 7;
    parameter COEFF_4 = 5;
    parameter COEFF_5 = 3;
    
    always @(posedge clk) begin
        if (!rst_n) begin
            delay_0 <= 0;
            delay_1 <= 0;
            delay_2 <= 0;
            delay_3 <= 0;
            delay_4 <= 0;
            delay_5 <= 0;
            accu <= 0;
            y <= 0;
        end
        else begin
            delay_0 <= x;
            delay_1 <= delay_0;
            delay_2 <= delay_1;
            delay_3 <= delay_2;
            delay_4 <= delay_3;
            delay_5 <= delay_4;
            
            accu <= (delay_0 * COEFF_0) + (delay_1 * COEFF_1) + (delay_2 * COEFF_2) +
                    (delay_3 * COEFF_3) + (delay_4 * COEFF_4) + (delay_5 * COEFF_5);
            
            y <= accu[15:0];
        end
    end
    
endmodule