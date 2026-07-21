module apiplain__firr36__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 36-element delay line (tap 0 = newest sample)
    reg [7:0] delay_line [0:35];
    
    // Sum accumulator (wide enough to avoid overflow)
    // Maximum value: sum(k=0..35) of (k+1)*255 = 255 * sum(k=1..36) k = 255 * 666 = 169830
    // This fits in 18 bits (2^18 = 262144), so use 18 bits for safety
    reg [17:0] sum;
    
    integer k;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line registers
            for (k = 0; k < 36; k = k + 1) begin
                delay_line[k] <= 8'b0;
            end
            y <= 16'b0;
        end
        else begin
            // Shift delay line and insert new sample
            delay_line[0] <= x;
            for (k = 1; k < 36; k = k + 1) begin
                delay_line[k] <= delay_line[k-1];
            end
            
            // Compute sum over all taps
            sum = 18'b0;
            for (k = 0; k < 36; k = k + 1) begin
                sum = sum + ((k + 1) * delay_line[k]);
            end
            
            // Output low 16 bits of sum
            y <= sum[15:0];
        end
    end

endmodule