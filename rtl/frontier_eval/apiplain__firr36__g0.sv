module apiplain__firr36__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line of 36 taps (8-bit each)
    reg [7:0] tap [0:35];
    
    // Intermediate signals for the sum
    integer i;
    reg [19:0] sum;  // Wide enough to hold product and sum
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all taps
            for (i = 0; i < 36; i = i + 1) begin
                tap[i] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift the delay line and insert new sample
            // tap[0] is the newest sample (current x)
            // tap[35] is the oldest sample
            for (i = 35; i > 0; i = i - 1) begin
                tap[i] <= tap[i-1];
            end
            tap[0] <= x;
            
            // Compute the sum: sum over k=0..35 of (k+1)*tap[k]
            sum = 20'd0;
            for (i = 0; i < 36; i = i + 1) begin
                sum = sum + ((i + 1) * tap[i]);
            end
            
            // Output the low 16 bits
            y <= sum[15:0];
        end
    end

endmodule