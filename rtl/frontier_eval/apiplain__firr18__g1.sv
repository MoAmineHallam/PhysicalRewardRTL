module apiplain__firr18__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 18 taps, 8 bits each
    reg [7:0] taps [0:17];
    
    // Internal sum (needs enough bits for 18 taps * max coefficient * max value)
    // Max coefficient = 18, max sample = 255
    // Max sum = 18 * 18 * 255 = 82620, needs 17 bits
    // Use 17 bits to be safe, then take lower 16 bits
    wire [16:0] sum;
    
    integer k;
    reg [16:0] sum_reg;
    
    // Compute sum using combinational logic
    always @(*) begin
        sum_reg = 0;
        for (k = 0; k < 18; k = k + 1) begin
            sum_reg = sum_reg + (taps[k] * (k + 1));
        end
    end
    
    assign sum = sum_reg;
    
    // Sequential logic: update delay line and output
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all taps
            for (k = 0; k < 18; k = k + 1) begin
                taps[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            for (k = 17; k > 0; k = k - 1) begin
                taps[k] <= taps[k-1];
            end
            taps[0] <= x;
            
            // Output the low 16 bits of the sum
            y <= sum[15:0];
        end
    end

endmodule