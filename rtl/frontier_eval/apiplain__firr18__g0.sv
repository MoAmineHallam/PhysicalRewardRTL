module apiplain__firr18__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 18-element delay line (tap 0 = newest sample)
    reg [7:0] delay_line [0:17];
    integer k;
    
    // Intermediate sum (wide enough to avoid overflow before truncation)
    reg [23:0] sum;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all state
            for (k = 0; k < 18; k = k + 1) begin
                delay_line[k] <= 8'b0;
            end
            y <= 16'b0;
        end else begin
            // Shift delay line and insert new sample
            // Tap 0 = newest = current x
            delay_line[0] <= x;
            for (k = 1; k < 18; k = k + 1) begin
                delay_line[k] <= delay_line[k-1];
            end
            
            // Compute sum of (k+1) * tap[k]
            sum = 24'b0;
            for (k = 0; k < 18; k = k + 1) begin
                sum = sum + (k + 1) * delay_line[k];
            end
            
            // Output low 16 bits of sum
            y <= sum[15:0];
        end
    end

endmodule