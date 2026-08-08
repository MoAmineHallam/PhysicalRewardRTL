module base__fir6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // FIR taps multipliers
    parameter h0 = 3;
    parameter h1 = 5;
    parameter h2 = 7;
    parameter h3 = 7;
    parameter h4 = 5;
    parameter h5 = 3;

    // Declare the 6-element delay line
    reg [7:0] delay_line[0:5];

    // Clear state to 0 on !rst_n
    always @ (posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 0;
            for (int i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 0;
            end
        end
        else begin
            // Shift the delay line
            delay_line[5] <= delay_line[4];
            delay_line[4] <= delay_line[3];
            delay_line[3] <= delay_line[2];
            delay_line[2] <= delay_line[1];
            delay_line[1] <= delay_line[0];
            delay_line[0] <= x;

            // Calculate the output
            y <= (delay_line[5] * h0) + (delay_line[4] * h1) + 
                 (delay_line[3] * h2) + (delay_line[2] * h3) + 
                 (delay_line[1] * h4) + (delay_line[0] * h5);
        end
    end
endmodule