module base__fir6_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [5:0];
    parameter [7:0] coeff_0 = 3;
    parameter [7:0] coeff_1 = 5;
    parameter [7:0] coeff_2 = 7;
    parameter [7:0] coeff_3 = 7;
    parameter [7:0] coeff_4 = 5;
    parameter [7:0] coeff_5 = 3;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 0;
            end
            y <= 0;
        end
        else begin
            delay_line[0] <= x;
            for (int i = 1; i < 6; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            y <= (delay_line[0] * coeff_0) + (delay_line[1] * coeff_1) + (delay_line[2] * coeff_2) +
                 (delay_line[3] * coeff_3) + (delay_line[4] * coeff_4) + (delay_line[5] * coeff_5);
        end
    end

endmodule