module base__fir40_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Define the coefficients
    parameter COEF_1 = 3;
    parameter COEF_2 = 5;
    parameter COEF_3 = 7;
    parameter COEF_4 = 9;
    parameter COEF_5 = 11;
    parameter COEF_6 = 13;
    parameter COEF_7 = 15;
    parameter COEF_8 = 17;
    parameter COEF_9 = 19;
    parameter COEF_10 = 21;
    parameter COEF_11 = 23;
    parameter COEF_12 = 25;
    parameter COEF_13 = 27;
    parameter COEF_14 = 29;
    parameter COEF_15 = 31;
    parameter COEF_16 = 33;
    parameter COEF_17 = 35;
    parameter COEF_18 = 37;
    parameter COEF_19 = 39;
    parameter COEF_20 = 41;
    parameter COEF_21 = 41;
    parameter COEF_22 = 39;
    parameter COEF_23 = 37;
    parameter COEF_24 = 35;
    parameter COEF_25 = 33;
    parameter COEF_26 = 31;
    parameter COEF_27 = 29;
    parameter COEF_28 = 27;
    parameter COEF_29 = 25;
    parameter COEF_30 = 23;
    parameter COEF_31 = 21;
    parameter COEF_32 = 19;
    parameter COEF_33 = 17;
    parameter COEF_34 = 15;
    parameter COEF_35 = 13;
    parameter COEF_36 = 11;
    parameter COEF_37 = 9;
    parameter COEF_38 = 7;
    parameter COEF_39 = 5;
    parameter COEF_40 = 3;

    // Define the delay line
    reg [7:0] delay_line [0:39];
    integer i;

    // Define the sum of products
    reg [39:0] sum_of_products;

    // Clear outputs on reset
    always @(negedge rst_n) begin
        y <= 0;
        for (i = 0; i < 40; i = i + 1) begin
            delay_line[i] <= 0;
        end
    end

    // Update the delay line and sum of products on every clock cycle
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
            for (i = 0; i < 40; i = i + 1) begin
                delay_line[i] <= 0;
            end
        end
        else begin
            sum_of_products <= x*COEF_1 + delay_line[0]*COEF_2 + delay_line[1]*COEF_3 + delay_line[2]*COEF_4 + delay_line[3]*COEF_5 + delay_line[4]*COEF_6 + delay_line[5]*COEF_7 + delay_line[6]*COEF_8 + delay_line[7]*COEF_9 + delay_line[8]*COEF_10 + delay_line[9]*COEF_11 + delay_line[10]*COEF_12 + delay_line[11]*COEF_13 + delay_line[12]*COEF_14 + delay_line[13]*COEF_15 + delay_line[14]*COEF_16 + delay_line[15]*COEF_17 + delay_line[16]*COEF_18 + delay_line[17]*COEF_19 + delay_line[18]*COEF_20 + delay_line[19]*COEF_21 + delay_line[20]*COEF_22 + delay_line[21]*COEF_23 + delay_line[22]*COEF_24 + delay_line[23]*COEF_25 + delay_line[24]*COEF_26 + delay_line[25]*COEF_27 + delay_line[26]*COEF_28 + delay_line[27]*COEF_29 + delay_line[28]*COEF_30 + delay_line[29]*COEF_31 + delay_line[30]*COEF_32 + delay_line[31]*COEF_33 + delay_line[32]*COEF_34 + delay_line[33]*COEF_35 + delay_line[34]*COEF_36 + delay_line[35]*COEF_37 + delay_line[36]*COEF_38 + delay_line[37]*COEF_39 + delay_line[38]*COEF_40;
            y <= sum_of_products[15:0];
            for (i = 39; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;
        end
    end

endmodule