module apiplain__firr40__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 40-element delay line (tap 0 = newest sample)
    reg [7:0] taps [0:39];
    
    // Internal sum variable (must hold enough bits: max tap value 40 * 255 * 40 ≈ 408000, need 19 bits)
    // Use 32-bit for safety
    reg [31:0] sum;
    
    integer k;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all taps
            for (k = 0; k < 40; k = k + 1) begin
                taps[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            // tap[0] = newest = current x; tap[39] = oldest
            for (k = 39; k > 0; k = k - 1) begin
                taps[k] <= taps[k-1];
            end
            taps[0] <= x;
            
            // Compute sum of (k+1)*tap[k]
            sum = 32'd0;
            for (k = 0; k < 40; k = k + 1) begin
                sum = sum + ((k+1) * taps[k]);
            end
            
            // Output low 16 bits
            y <= sum[15:0];
        end
    end
    
endmodule