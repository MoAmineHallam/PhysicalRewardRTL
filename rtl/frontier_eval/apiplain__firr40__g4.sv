module apiplain__firr40__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 40 taps, each 8 bits wide
    reg [7:0] tap [0:39];
    integer k;
    
    // Intermediate sum (needs enough bits: 8-bit data * 40 coefficients max 40*40=1600, 
    // but coefficient (k+1) max = 40, so max product = 40*255 = 10200. 
    // Sum of 40 such products max = 40*10200 = 408000, fits in 19 bits.
    // We'll use 19 bits for sum, then take low 16 bits.
    reg [18:0] sum;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line taps
            for (k = 0; k < 40; k = k + 1) begin
                tap[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line: new sample x becomes tap[0], old samples shift right
            tap[0] <= x;
            for (k = 1; k < 40; k = k + 1) begin
                tap[k] <= tap[k-1];
            end
            
            // Compute sum of (k+1) * tap[k] for k=0..39
            sum = 19'd0;
            for (k = 0; k < 40; k = k + 1) begin
                // Multiply (k+1) by tap[k] (both unsigned)
                sum = sum + ((k+1) * tap[k]);
            end
            
            // Output low 16 bits of sum
            y <= sum[15:0];
        end
    end

endmodule