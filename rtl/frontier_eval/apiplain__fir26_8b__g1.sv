module apiplain__fir26_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 26 elements of 8-bit unsigned samples
    reg [7:0] delay_line [25:0];
    
    // Fixed coefficients (symmetric, 26 taps)
    // To match [3,5,7,9,11,13,15,17,19,21,23,25,27,27,25,23,21,19,17,15,13,11,9,7,5,3]
    wire [4:0] coeff [25:0];
    assign coeff[0]  = 5'd3;
    assign coeff[1]  = 5'd5;
    assign coeff[2]  = 5'd7;
    assign coeff[3]  = 5'd9;
    assign coeff[4]  = 5'd11;
    assign coeff[5]  = 5'd13;
    assign coeff[6]  = 5'd15;
    assign coeff[7]  = 5'd17;
    assign coeff[8]  = 5'd19;
    assign coeff[9]  = 5'd21;
    assign coeff[10] = 5'd23;
    assign coeff[11] = 5'd25;
    assign coeff[12] = 5'd27;
    assign coeff[13] = 5'd27;
    assign coeff[14] = 5'd25;
    assign coeff[15] = 5'd23;
    assign coeff[16] = 5'd21;
    assign coeff[17] = 5'd19;
    assign coeff[18] = 5'd17;
    assign coeff[19] = 5'd15;
    assign coeff[20] = 5'd13;
    assign coeff[21] = 5'd11;
    assign coeff[22] = 5'd9;
    assign coeff[23] = 5'd7;
    assign coeff[24] = 5'd5;
    assign coeff[25] = 5'd3;

    // Index for looping
    integer i;

    // Sum of products (wide enough to avoid overflow before truncation)
    reg [15:0] sum;

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
            sum = 16'd0;
            for (i = 0; i < 26; i = i + 1) begin
                sum = sum + (delay_line[i] * coeff[i]);
            end

            // Output the low 16 bits
            y <= sum;
        end
    end

endmodule