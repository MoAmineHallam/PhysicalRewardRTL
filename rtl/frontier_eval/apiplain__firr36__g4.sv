module apiplain__firr36__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 36-element delay line (tap 0 = newest sample)
    reg [7:0] delay_line [0:35];
    integer i;
    
    // Internal sum (wide enough to avoid overflow before truncation)
    wire [21:0] sum;
    
    // Compute the sum over k=0..35 of (k+1)*tap[k]
    // Each term: (k+1) up to 36 requires 6 bits, tap[k] is 8 bits
    // Product up to 14 bits, sum of 36 terms up to ~20 bits
    assign sum =  (36 * delay_line[35]) + (35 * delay_line[34]) + 
                  (34 * delay_line[33]) + (33 * delay_line[32]) + 
                  (32 * delay_line[31]) + (31 * delay_line[30]) + 
                  (30 * delay_line[29]) + (29 * delay_line[28]) + 
                  (28 * delay_line[27]) + (27 * delay_line[26]) + 
                  (26 * delay_line[25]) + (25 * delay_line[24]) + 
                  (24 * delay_line[23]) + (23 * delay_line[22]) + 
                  (22 * delay_line[21]) + (21 * delay_line[20]) + 
                  (20 * delay_line[19]) + (19 * delay_line[18]) + 
                  (18 * delay_line[17]) + (17 * delay_line[16]) + 
                  (16 * delay_line[15]) + (15 * delay_line[14]) + 
                  (14 * delay_line[13]) + (13 * delay_line[12]) + 
                  (12 * delay_line[11]) + (11 * delay_line[10]) + 
                  (10 * delay_line[9])  + (9  * delay_line[8])  + 
                  (8  * delay_line[7])  + (7  * delay_line[6])  + 
                  (6  * delay_line[5])  + (5  * delay_line[4])  + 
                  (4  * delay_line[3])  + (3  * delay_line[2])  + 
                  (2  * delay_line[1])  + (1  * delay_line[0]);
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line elements and output
            for (i = 0; i < 36; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            delay_line[0] <= x;
            for (i = 1; i < 36; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            // Output low 16 bits of the sum
            y <= sum[15:0];
        end
    end

endmodule