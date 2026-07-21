module apiplain__fir36_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line of past 36 samples
    reg [7:0] delay_line [0:35];
    
    // Fixed coefficients - symmetric
    // Note: inputs are unsigned 8-bit, coefficients fit in 6 bits max
    // Maximum product: 37 * 255 = 9435 (14 bits)
    // Sum of 36 products maximum: 36 * 9435 = 339660 (19 bits)
    // We take low 16 bits of the sum
    
    integer i;
    reg [18:0] sum;  // 19 bits to hold full sum without overflow
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line
            for (i = 0; i < 36; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            y <= 16'd0;
        end
        else begin
            // Shift delay line and insert new sample
            for (i = 35; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;
            
            // Compute sum of products
            sum = delay_line[0] * 8'd3;
            sum = sum + delay_line[1] * 8'd5;
            sum = sum + delay_line[2] * 8'd7;
            sum = sum + delay_line[3] * 8'd9;
            sum = sum + delay_line[4] * 8'd11;
            sum = sum + delay_line[5] * 8'd13;
            sum = sum + delay_line[6] * 8'd15;
            sum = sum + delay_line[7] * 8'd17;
            sum = sum + delay_line[8] * 8'd19;
            sum = sum + delay_line[9] * 8'd21;
            sum = sum + delay_line[10] * 8'd23;
            sum = sum + delay_line[11] * 8'd25;
            sum = sum + delay_line[12] * 8'd27;
            sum = sum + delay_line[13] * 8'd29;
            sum = sum + delay_line[14] * 8'd31;
            sum = sum + delay_line[15] * 8'd33;
            sum = sum + delay_line[16] * 8'd35;
            sum = sum + delay_line[17] * 8'd37;
            sum = sum + delay_line[18] * 8'd37;
            sum = sum + delay_line[19] * 8'd35;
            sum = sum + delay_line[20] * 8'd33;
            sum = sum + delay_line[21] * 8'd31;
            sum = sum + delay_line[22] * 8'd29;
            sum = sum + delay_line[23] * 8'd27;
            sum = sum + delay_line[24] * 8'd25;
            sum = sum + delay_line[25] * 8'd23;
            sum = sum + delay_line[26] * 8'd21;
            sum = sum + delay_line[27] * 8'd19;
            sum = sum + delay_line[28] * 8'd17;
            sum = sum + delay_line[29] * 8'd15;
            sum = sum + delay_line[30] * 8'd13;
            sum = sum + delay_line[31] * 8'd11;
            sum = sum + delay_line[32] * 8'd9;
            sum = sum + delay_line[33] * 8'd7;
            sum = sum + delay_line[34] * 8'd5;
            sum = sum + delay_line[35] * 8'd3;
            
            // Output low 16 bits of the sum
            y <= sum[15:0];
        end
    end

endmodule