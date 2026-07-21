module apiplain__firr6__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    // 6-element delay line (tap 0 = newest sample)
    reg [7:0] tap [0:5];
    integer k;
    
    // Temporary sum (needs enough bits: max sum = 6*255 = 1530, 
    // times coefficients 1..6 gives max = 255*(1+2+3+4+5+6) = 255*21 = 5355,
    // fits in 13 bits, but we store 16-bit for safety)
    reg [15:0] sum;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line elements
            for (k = 0; k < 6; k = k + 1)
                tap[k] <= 8'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample at tap 0
            tap[0] <= x;
            for (k = 1; k < 6; k = k + 1)
                tap[k] <= tap[k-1];
            
            // Compute sum of (k+1)*tap[k]
            sum = 16'd0;
            for (k = 0; k < 6; k = k + 1)
                sum = sum + ((k + 1) * tap[k]);
            
            // Output low 16 bits of sum
            y <= sum;
        end
    end
endmodule