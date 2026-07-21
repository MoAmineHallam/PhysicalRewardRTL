module apiplain__firr6__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 6 taps, each 8 bits
    reg [7:0] tap [0:5];
    
    // Intermediate sum (needs enough bits to hold sum of 6 products)
    // Max product = 6 * 255 = 1530, max sum = sum(k=1..6 of k*255) = 255*(1+2+3+4+5+6) = 255*21 = 5355
    // So we need at least 13 bits; use full 16-bit for safety
    reg [15:0] sum;
    
    integer k;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line taps
            for (k = 0; k < 6; k = k + 1) begin
                tap[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            // tap[0] is newest sample (current x)
            // tap[5] is oldest sample
            tap[0] <= x;
            for (k = 1; k < 6; k = k + 1) begin
                tap[k] <= tap[k-1];
            end
            
            // Compute FIR output: sum over k=0..5 of (k+1)*tap[k]
            sum = 16'd0;
            for (k = 0; k < 6; k = k + 1) begin
                sum = sum + ((k + 1) * tap[k]);
            end
            y <= sum[15:0];
        end
    end

endmodule