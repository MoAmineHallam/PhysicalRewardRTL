module apiplain__firr10__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 10 elements, each 8 bits
    reg [7:0]  taps [0:9];
    
    // Sum accumulator (wide enough to hold sum of 10 products)
    // Max product: 10 * 255 = 2550, max sum of 10 products: 10 * 2550 = 25500 (fits in 15 bits)
    // Using 16 bits is sufficient
    reg [15:0] sum;
    integer k;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all taps and output
            for (k = 0; k < 10; k = k + 1) begin
                taps[k] <= 8'd0;
            end
            y <= 16'd0;
            sum <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            // tap[0] gets newest sample (current x)
            for (k = 9; k > 0; k = k - 1) begin
                taps[k] <= taps[k-1];
            end
            taps[0] <= x;
            
            // Compute sum: for each tap k, multiply by coefficient (k+1)
            sum <= (10'd1 * taps[0]) + 
                   (10'd2 * taps[1]) + 
                   (10'd3 * taps[2]) + 
                   (10'd4 * taps[3]) + 
                   (10'd5 * taps[4]) + 
                   (10'd6 * taps[5]) + 
                   (10'd7 * taps[6]) + 
                   (10'd8 * taps[7]) + 
                   (10'd9 * taps[8]) + 
                   (10'd10 * taps[9]);
            
            // Output the low 16 bits of the sum
            y <= sum;
        end
    end

endmodule