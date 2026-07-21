module apiplain__firr10__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 10-element delay line (tap 0 = newest = current x)
    reg [7:0] taps [0:9];
    
    // Internal signals for accumulation
    wire [15:0] sum;
    integer k;
    
    // Compute the sum of (k+1)*tap[k] for k=0..9
    // Use intermediate wide enough to avoid overflow during computation
    wire [23:0] sum_full;
    
    assign sum_full = 
        (10 * taps[9]) + 
        (9  * taps[8]) + 
        (8  * taps[7]) + 
        (7  * taps[6]) + 
        (6  * taps[5]) + 
        (5  * taps[4]) + 
        (4  * taps[3]) + 
        (3  * taps[2]) + 
        (2  * taps[1]) + 
        (1  * taps[0]);
    
    assign sum = sum_full[15:0];
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all state
            for (k = 0; k < 10; k = k + 1) begin
                taps[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            // tap[0] = newest sample
            // tap[9] = oldest sample
            taps[9] <= taps[8];
            taps[8] <= taps[7];
            taps[7] <= taps[6];
            taps[6] <= taps[5];
            taps[5] <= taps[4];
            taps[4] <= taps[3];
            taps[3] <= taps[2];
            taps[2] <= taps[1];
            taps[1] <= taps[0];
            taps[0] <= x;
            
            // Registered output
            y <= sum;
        end
    end
    
endmodule