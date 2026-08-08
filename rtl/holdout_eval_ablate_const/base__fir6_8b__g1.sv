module base__fir6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    parameter COEFF_0 = 3;
    parameter COEFF_1 = 5;
    parameter COEFF_2 = 7;
    parameter COEFF_3 = 7;
    parameter COEFF_4 = 5;
    parameter COEFF_5 = 3;

    reg [7:0] delay_line [0:5];
    integer i;
    
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
            for (i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 0;
            end
        end else begin
            // Shift the delay line and insert new sample
            for (i = 5; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;
            
            // Compute the output using the FIR filter
            y <= (delay_line[0] * COEFF_0) + 
                 (delay_line[1] * COEFF_1) + 
                 (delay_line[2] * COEFF_2) + 
                 (delay_line[3] * COEFF_3) + 
                 (delay_line[4] * COEFF_4) + 
                 (delay_line[5] * COEFF_5);
        end
    end

endmodule