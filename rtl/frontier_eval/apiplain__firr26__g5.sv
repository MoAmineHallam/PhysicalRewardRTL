module apiplain__firr26__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 26 elements of 8-bit samples
    reg [7:0] delay_line [0:25];
    
    // Intermediate sum variable
    wire [25:0] sum;
    
    integer k;
    
    // Compute the sum: Σ (k+1) * tap[k] for k=0..25
    // Since coefficients are (k+1), we can generate the sum combinatorially
    assign sum = 26'd0  // This would be overwritten below
                ;
    
    // Generate the summation
    wire [25:0] partial_sum [0:25];
    reg [25:0] sum_reg;
    
    // Combinational sum computation
    always @(*) begin
        sum_reg = 26'd0;
        for (k = 0; k < 26; k = k + 1) begin
            sum_reg = sum_reg + (delay_line[k] * (k + 1));
        end
    end
    
    // Register the output (low 16 bits of the sum)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'd0;
            // Clear delay line
            for (k = 0; k < 26; k = k + 1) begin
                delay_line[k] <= 8'd0;
            end
        end else begin
            // Shift delay line and insert new sample
            for (k = 25; k > 0; k = k - 1) begin
                delay_line[k] <= delay_line[k-1];
            end
            delay_line[0] <= x;
            
            // Output the low 16 bits of the sum
            y <= sum_reg[15:0];
        end
    end

endmodule