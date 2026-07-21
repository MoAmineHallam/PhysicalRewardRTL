module apiplain__fir26_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 26-element delay line of past samples (8-bit each)
    reg [7:0] delay_line [0:25];
    
    // Fixed coefficients (symmetric, 26 taps)
    // Coeffs: [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 
    //           27, 25, 23, 21, 19, 17, 15, 13, 11, 9, 7, 5, 3]
    wire [4:0] coeffs [0:25];
    assign coeffs[0]  = 5'd3;
    assign coeffs[1]  = 5'd5;
    assign coeffs[2]  = 5'd7;
    assign coeffs[3]  = 5'd9;
    assign coeffs[4]  = 5'd11;
    assign coeffs[5]  = 5'd13;
    assign coeffs[6]  = 5'd15;
    assign coeffs[7]  = 5'd17;
    assign coeffs[8]  = 5'd19;
    assign coeffs[9]  = 5'd21;
    assign coeffs[10] = 5'd23;
    assign coeffs[11] = 5'd25;
    assign coeffs[12] = 5'd27;
    assign coeffs[13] = 5'd27;
    assign coeffs[14] = 5'd25;
    assign coeffs[15] = 5'd23;
    assign coeffs[16] = 5'd21;
    assign coeffs[17] = 5'd19;
    assign coeffs[18] = 5'd17;
    assign coeffs[19] = 5'd15;
    assign coeffs[20] = 5'd13;
    assign coeffs[21] = 5'd11;
    assign coeffs[22] = 5'd9;
    assign coeffs[23] = 5'd7;
    assign coeffs[24] = 5'd5;
    assign coeffs[25] = 5'd3;

    integer i;
    reg [16:0] sum;  // 17-bit intermediate to prevent overflow before truncation

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line and output
            for (i = 0; i < 26; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            for (i = 25; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;
            
            // Compute sum of products
            sum = 17'd0;
            for (i = 0; i < 26; i = i + 1) begin
                sum = sum + (delay_line[i] * coeffs[i]);
            end
            
            // Output low 16 bits of the sum
            y <= sum[15:0];
        end
    end

endmodule