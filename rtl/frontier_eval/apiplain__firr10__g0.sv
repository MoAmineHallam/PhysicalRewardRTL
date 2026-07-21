module apiplain__firr10__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 10-element delay line (tap 0 = newest sample)
    reg [7:0] tap [0:9];
    
    // Internal sum variable (wide enough to hold the maximum sum)
    // Max value: sum of (k+1)*255 for k=0..9 = 255 * (1+2+...+10) = 255 * 55 = 14025
    // 14 bits is enough, but we use wider for safety
    reg [15:0] sum;
    
    integer k;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line elements
            for (k = 0; k < 10; k = k + 1) begin
                tap[k] <= 8'd0;
            end
            y <= 16'd0;
        end
        else begin
            // Shift delay line: tap[0] gets newest sample x
            // tap[i] gets old tap[i-1]
            for (k = 9; k > 0; k = k - 1) begin
                tap[k] <= tap[k-1];
            end
            tap[0] <= x;
            
            // Compute sum: (k+1) * tap[k] for k=0..9
            sum = 16'd0;
            for (k = 0; k < 10; k = k + 1) begin
                sum = sum + ((k+1) * tap[k]);
            end
            
            // Output the low 16 bits of the sum
            y <= sum;
        end
    end

endmodule