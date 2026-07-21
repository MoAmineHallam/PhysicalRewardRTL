module apiplain__fir26_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line for 26 past samples, shift register style
    reg [7:0] delay_line [0:25];
    integer i;

    // Coefficient array (symmetric)
    wire [4:0] coeff [0:25];
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

    // Registered sum and output
    reg [12:0] sum;  // Sufficient width: max product = 27*255 = 6885, sum of 26 such = ~179k < 2^18, so 18 bits needed, but we'll compute wider
    reg [17:0] sum_full;  // 18 bits to hold full sum without overflow
    integer j;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line
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
            sum_full = 18'd0;
            for (j = 0; j < 26; j = j + 1) begin
                sum_full = sum_full + (delay_line[j] * coeff[j]);
            end

            // Output low 16 bits
            y <= sum_full[15:0];
        end
    end

endmodule