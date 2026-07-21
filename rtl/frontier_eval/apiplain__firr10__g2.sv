module apiplain__firr10__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 10-element delay line of past samples (tap 0 = newest = current x)
    reg [7:0] taps [0:9];
    
    // Internal sum (wide enough to hold sum of products without overflow)
    // Maximum product: 10 * 255 = 2550, max sum of 10 such products = 25500
    // So we need at least 15 bits; we'll use 32 for safety
    reg [31:0] sum;
    
    integer k;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all state
            for (k = 0; k < 10; k = k + 1) begin
                taps[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample at tap 0
            // Shift from tap 8 down to tap 0
            for (k = 9; k > 0; k = k - 1) begin
                taps[k] <= taps[k-1];
            end
            taps[0] <= x;
            
            // Compute sum of (k+1)*tap[k] for k=0..9
            sum = 32'd0;
            for (k = 0; k < 10; k = k + 1) begin
                sum = sum + (k+1) * taps[k];
            end
            
            // Output low 16 bits
            y <= sum[15:0];
        end
    end

endmodule