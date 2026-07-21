module apiplain__firr40__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 40 elements, 8-bit each
    reg [7:0] delay_line [0:39];
    
    // Internal accumulator - needs enough bits for sum of (k+1)*tap[k]
    // Maximum value: sum of (k+1)*255 for k=0..39
    // = 255 * sum of (k+1) for k=0..39 = 255 * 820 = 209100
    // This fits in 18 bits (262143 max), but using 32 bits for safety
    reg [31:0] sum;
    
    integer k;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line elements
            for (k = 0; k < 40; k = k + 1) begin
                delay_line[k] <= 8'b0;
            end
            y <= 16'b0;
        end else begin
            // Shift delay line and insert new sample
            for (k = 39; k > 0; k = k - 1) begin
                delay_line[k] <= delay_line[k-1];
            end
            delay_line[0] <= x;
            
            // Compute sum (could also be done in a separate block for clarity)
            sum = 0;
            for (k = 0; k < 40; k = k + 1) begin
                sum = sum + ((k+1) * delay_line[k]);
            end
            
            // Output lower 16 bits
            y <= sum[15:0];
        end
    end

endmodule