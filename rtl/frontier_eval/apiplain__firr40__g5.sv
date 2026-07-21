module apiplain__firr40__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 40-element delay line (tap 0 = newest = current x)
    reg [7:0] taps [0:39];
    
    // Internal variables for computation
    integer k;
    reg [23:0] sum;  // Wide enough to hold sum of 40 products (max: 40*40*255 = 408,000)
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all taps
            for (k = 0; k < 40; k = k + 1) begin
                taps[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line: tap[0] gets new sample, others shift right
            taps[0] <= x;
            for (k = 1; k < 40; k = k + 1) begin
                taps[k] <= taps[k-1];
            end
            
            // Compute sum = Σ (k+1) * taps[k] for k=0..39
            sum = 24'd0;
            for (k = 0; k < 40; k = k + 1) begin
                sum = sum + ((k + 1) * taps[k]);
            end
            
            // Output low 16 bits of the sum
            y <= sum[15:0];
        end
    end

endmodule