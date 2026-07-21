module apiplain__firr26__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line for 26 samples (tap 0 = newest = current x)
    reg [7:0] delay_line [0:25];
    
    // Synthesis variable for accumulation
    integer k;
    reg [25:0] sum;  // Need enough bits: max sum = 26 * 25 * 255 ≈ 165,750 which needs 18 bits.
                      // Using 26 bits for safety with intermediate calculations
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all state
            for (k = 0; k < 26; k = k + 1) begin
                delay_line[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            for (k = 25; k > 0; k = k - 1) begin
                delay_line[k] <= delay_line[k-1];
            end
            delay_line[0] <= x;
            
            // Compute sum with coefficients (k+1) for tap k
            sum = 26'd0;
            for (k = 0; k < 26; k = k + 1) begin
                sum = sum + ((k + 1) * delay_line[k]);
            end
            
            // Take low 16 bits
            y <= sum[15:0];
        end
    end
    
endmodule