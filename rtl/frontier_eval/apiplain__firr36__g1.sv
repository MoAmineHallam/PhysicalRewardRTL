module apiplain__firr36__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 36-element delay line (tap 0 = newest sample)
    reg [7:0] delay_line [0:35];
    
    // Internal signals for accumulation
    integer k;
    reg [23:0] sum;  // Wide enough to hold the full sum before truncation
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line elements
            for (k = 0; k < 36; k = k + 1) begin
                delay_line[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            // tap[0] = current x, tap[1] = previous x, etc.
            for (k = 35; k > 0; k = k - 1) begin
                delay_line[k] <= delay_line[k-1];
            end
            delay_line[0] <= x;
            
            // Compute sum: low 16 bits of (k+1)*delay_line[k]
            sum = 24'd0;
            for (k = 0; k < 36; k = k + 1) begin
                sum = sum + ((k + 1) * delay_line[k]);
            end
            
            // Output the low 16 bits
            y <= sum[15:0];
        end
    end

endmodule