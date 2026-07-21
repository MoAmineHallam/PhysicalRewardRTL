module apiplain__firr6__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 6-element delay line (tap 0 = newest sample)
    reg [7:0] delay_line [0:5];
    
    // Intermediate sum (needs enough bits for 6 multiplications)
    // Max value: sum of (k+1)*255 for k=0..5 = 255*(1+2+3+4+5+6) = 255*21 = 5355
    // This fits in 13 bits, but we'll use wider for safety
    reg [15:0] sum;
    
    integer k;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line registers
            for (k = 0; k < 6; k = k + 1) begin
                delay_line[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample at tap 0
            delay_line[0] <= x;
            for (k = 1; k < 6; k = k + 1) begin
                delay_line[k] <= delay_line[k-1];
            end
            
            // Compute the sum
            sum = 16'd0;
            for (k = 0; k < 6; k = k + 1) begin
                sum = sum + ((k+1) * delay_line[k]);
            end
            
            // Output the low 16 bits
            y <= sum;
        end
    end

endmodule