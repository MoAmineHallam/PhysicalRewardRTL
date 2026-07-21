module apiplain__firr40__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 40 elements, 8 bits each
    reg [7:0] delay_line [0:39];
    integer k;
    
    // Sum accumulator (needs enough bits: max sum = sum_{k=0}^{39} (k+1)*255 
    // = 255 * sum_{k=1}^{40} k = 255 * 820 = 209100, fits in 18 bits)
    reg [17:0] sum;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line elements
            for (k = 0; k < 40; k = k + 1) begin
                delay_line[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line: tap0 gets new input x
            delay_line[0] <= x;
            for (k = 1; k < 40; k = k + 1) begin
                delay_line[k] <= delay_line[k-1];
            end
            
            // Compute sum of (k+1)*tap[k]
            sum = 18'd0;
            for (k = 0; k < 40; k = k + 1) begin
                sum = sum + (delay_line[k] * (k+1));
            end
            
            // Output low 16 bits of sum
            y <= sum[15:0];
        end
    end

endmodule