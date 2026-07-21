module apiplain__firr18__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 18 taps of 8-bit unsigned samples
    reg [7:0] taps [0:17];
    
    // Internal accumulator (wide enough to avoid overflow before truncation)
    // Max value: sum(k=0..17) of (k+1)*255 = sum(k=1..18) k*255
    // = 255 * (18*19/2) = 255 * 171 = 43605, which fits in 16 bits
    // But keep it wider for synthesis safety
    reg [15:0] sum;
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line taps
            for (i = 0; i < 18; i = i + 1)
                taps[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line: tap[0] = current x, tap[k] = previous tap[k-1]
            taps[0] <= x;
            for (i = 1; i < 18; i = i + 1)
                taps[i] <= taps[i-1];
            
            // Compute weighted sum
            sum = 16'd0;
            for (i = 0; i < 18; i = i + 1)
                sum = sum + (taps[i] * (i + 1));
            
            // Output registered result
            y <= sum;
        end
    end

endmodule