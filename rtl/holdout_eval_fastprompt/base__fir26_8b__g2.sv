module base__fir26_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    parameter WIDTH = 8;
    parameter TAPS = 26;
    parameter COEFF_WIDTH = 4;
    parameter DATA_WIDTH = 16;
    parameter ADDR_WIDTH = 5;
    
    localparam COEFF_A = 3;
    localparam COEFF_B = 5;
    localparam COEFF_C = 7;
    localparam COEFF_D = 9;
    localparam COEFF_E = 11;
    localparam COEFF_F = 13;
    localparam COEFF_G = 15;
    localparam COEFF_H = 17;
    localparam COEFF_I = 19;
    localparam COEFF_J = 21;
    localparam COEFF_K = 23;
    localparam COEFF_L = 25;
    localparam COEFF_M = 27;
    localparam COEFF_N = 27;
    localparam COEFF_O = 25;
    localparam COEFF_P = 23;
    localparam COEFF_Q = 21;
    localparam COEFF_R = 19;
    localparam COEFF_S = 17;
    localparam COEFF_T = 15;
    localparam COEFF_U = 13;
    localparam COEFF_V = 11;
    localparam COEFF_W = 9;
    localparam COEFF_X = 7;
    localparam COEFF_Y = 5;
    localparam COEFF_Z = 3;
    
    reg [WIDTH-1:0] delay_line [0:TAPS-1];
    reg [DATA_WIDTH-1:0] acc;
    
    integer i;
    
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
            acc <= 0;
            for (i = 0; i < TAPS; i = i + 1) begin
                delay_line[i] <= 0;
            end
        end else begin
            // Shift samples to delay line
            delay_line[0] <= x;
            for (i = 1; i < TAPS; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            
            // Multiply and accumulate samples
            acc <= (delay_line[0] * COEFF_Z) +
                   (delay_line[1] * COEFF_Y) +
                   (delay_line[2] * COEFF_X) +
                   (delay_line[3] * COEFF_W) +
                   (delay_line[4] * COEFF_V) +
                   (delay_line[5] * COEFF_U) +
                   (delay_line[6] * COEFF_T) +
                   (delay_line[7] * COEFF_S) +
                   (delay_line[8] * COEFF_R) +
                   (delay_line[9] * COEFF_Q) +
                   (delay_line[10] * COEFF_P) +
                   (delay_line[11] * COEFF_O) +
                   (delay_line[12] * COEFF_N) +
                   (delay_line[13] * COEFF_M) +
                   (delay_line[14] * COEFF_L) +
                   (delay_line[15] * COEFF_K) +
                   (delay_line[16] * COEFF_J) +
                   (delay_line[17] * COEFF_I) +
                   (delay_line[18] * COEFF_H) +
                   (delay_line[19] * COEFF_G) +
                   (delay_line[20] * COEFF_F) +
                   (delay_line[21] * COEFF_E) +
                   (delay_line[22] * COEFF_D) +
                   (delay_line[23] * COEFF_C) +
                   (delay_line[24] * COEFF_B) +
                   (delay_line[25] * COEFF_A);
            y <= acc[DATA_WIDTH-1:0];
        end
    end

endmodule