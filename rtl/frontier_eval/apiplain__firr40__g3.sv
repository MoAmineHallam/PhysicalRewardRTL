module apiplain__firr40__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line: 40 elements of 8-bit unsigned samples
    // tap[0] = newest sample (current x)
    reg [7:0] tap [0:39];
    
    // Combined sum variable (wide enough to hold full product sum)
    // Maximum product: 39*255 = 9945, sum of 40 such products max = ~397k
    // 19 bits is sufficient, use 32 bits for safety
    reg [31:0] sum;
    
    integer k;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line elements
            for (k = 0; k < 40; k = k + 1) begin
                tap[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            // tap[0] = newest, tap[39] = oldest
            for (k = 39; k > 0; k = k - 1) begin
                tap[k] <= tap[k-1];
            end
            tap[0] <= x;
            
            // Compute sum of (k+1)*tap[k] for k=0..39
            // coefficient for tap k is (k+1)
            sum = 32'd0;
            for (k = 0; k < 40; k = k + 1) begin
                sum = sum + ((k+1) * tap[k]);
            end
            
            // Take low 16 bits as output
            y <= sum[15:0];
        end
    end

endmodule