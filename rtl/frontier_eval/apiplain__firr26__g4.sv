module apiplain__firr26__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line of 26 taps, 8-bit each
    reg [7:0] taps [0:25];
    
    // Combined product and accumulation logic
    integer k;
    reg [25:0] sum;  // Wide enough to hold (k+1)*255 summed for k=0..25
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all taps to zero
            for (k = 0; k < 26; k = k + 1) begin
                taps[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            for (k = 25; k > 0; k = k - 1) begin
                taps[k] <= taps[k-1];
            end
            taps[0] <= x;
            
            // Compute sum of (k+1)*tap[k]
            sum = 0;
            for (k = 0; k < 26; k = k + 1) begin
                sum = sum + (k + 1) * taps[k];
            end
            y <= sum[15:0];
        end
    end

endmodule