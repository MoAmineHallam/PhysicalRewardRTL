module apiplain__firr26__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 26-element delay line for past samples
    // tap[0] = newest sample = current x
    // tap[25] = oldest sample
    reg [7:0] tap [0:25];
    
    // Sum of products: (k+1)*tap[k] for k=0..25
    // Maximum value: 26 * 255 = 6630, sum of 26 such terms max ~ 26*6630 = 172380
    // This fits in 18 bits, so we use 18-bit intermediate
    wire [17:0] sum;
    
    integer k;
    reg [17:0] sum_temp;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line
            for (k = 0; k < 26; k = k + 1) begin
                tap[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            for (k = 25; k > 0; k = k - 1) begin
                tap[k] <= tap[k-1];
            end
            tap[0] <= x;
            
            // Compute sum of products
            sum_temp = 18'd0;
            for (k = 0; k < 26; k = k + 1) begin
                sum_temp = sum_temp + (k + 1) * tap[k];
            end
            
            // Output lower 16 bits
            y <= sum_temp[15:0];
        end
    end

endmodule