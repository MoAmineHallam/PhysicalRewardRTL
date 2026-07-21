module apiplain__firr18__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 18-element delay line: tap[0]=newest, tap[17]=oldest
    reg [7:0] tap [0:17];
    integer k;
    
    // Temporary sum (needs enough bits for worst-case:
    // max x = 255, max coefficient = 18, sum of 18 terms:
    // 255 * (1+2+...+18) = 255 * 171 = 43605, fits in 16 bits
    // But we keep intermediate in wider for safety
    reg [15:0] sum;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all taps and output
            for (k = 0; k < 18; k = k + 1)
                tap[k] <= 8'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            for (k = 17; k > 0; k = k - 1)
                tap[k] <= tap[k-1];
            tap[0] <= x;
            
            // Compute FIR sum: y = sum (k+1)*tap[k]
            sum = 16'd0;
            for (k = 0; k < 18; k = k + 1)
                sum = sum + ( (k+1) * tap[k] );
            y <= sum;
        end
    end

endmodule