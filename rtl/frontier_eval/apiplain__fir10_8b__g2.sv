module apiplain__fir10_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Fixed coefficients [3, 5, 7, 9, 11, 11, 9, 7, 5, 3]
    // 10-tap direct-form FIR filter

    // Delay line for past 10 samples (including current input)
    reg [7:0] delay_line [9:0];
    integer i;

    // Sum of products (wide enough to avoid overflow before truncation)
    wire [15:0] sum;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1)
                delay_line[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            delay_line[0] <= x;
            for (i = 1; i < 10; i = i + 1)
                delay_line[i] <= delay_line[i-1];
            
            // Registered output
            y <= sum;
        end
    end

    // Compute sum of products (combinational)
    assign sum = (delay_line[0] * 3) + (delay_line[1] * 5) + (delay_line[2] * 7) + 
                 (delay_line[3] * 9) + (delay_line[4] * 11) + (delay_line[5] * 11) + 
                 (delay_line[6] * 9) + (delay_line[7] * 7) + (delay_line[8] * 5) + 
                 (delay_line[9] * 3);

endmodule