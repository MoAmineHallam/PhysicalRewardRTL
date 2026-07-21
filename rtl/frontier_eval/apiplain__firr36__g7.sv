module apiplain__firr36__g7 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line of 36 samples (tap 0 = newest = current x)
    reg [7:0] taps [0:35];
    
    // Internal accumulation (wide enough to avoid overflow)
    // Max sum: sum_{k=0}^{35} (k+1)*255 = 255 * sum_{k=1}^{36} k = 255 * 666 = 169830
    // 169830 fits in 18 bits (2^18 = 262144)
    reg [17:0] sum;
    
    integer k;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all state
            for (k = 0; k < 36; k = k + 1) begin
                taps[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            // tap[0] is newest, tap[35] is oldest
            taps[0] <= x;
            for (k = 1; k < 36; k = k + 1) begin
                taps[k] <= taps[k-1];
            end
            
            // Compute the sum: sum_{k=0}^{35} (k+1)*tap[k]
            sum = 18'd0;
            for (k = 0; k < 36; k = k + 1) begin
                sum = sum + ((k + 1) * taps[k]);
            end
            
            // Output low 16 bits of the sum
            y <= sum[15:0];
        end
    end

endmodule