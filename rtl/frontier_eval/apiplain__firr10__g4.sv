module apiplain__firr10__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 10-element delay line (tap 0 = newest = current x)
    reg [7:0] tap [0:9];
    
    // Internal compute signals
    reg [15:0] sum;
    integer k;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all state
            for (k = 0; k < 10; k = k + 1) begin
                tap[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            for (k = 9; k > 0; k = k - 1) begin
                tap[k] <= tap[k-1];
            end
            tap[0] <= x;
            
            // Compute sum of (k+1) * tap[k]
            sum = 16'd0;
            for (k = 0; k < 10; k = k + 1) begin
                sum = sum + ((k + 1) * tap[k]);
            end
            
            // Output the low 16 bits (automatically via sum being 16-bit)
            y <= sum;
        end
    end

endmodule