module apiplain__fir6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 6-element delay line for past samples
    reg [7:0] delay_line [0:5];
    
    // Sum of products - need enough bits to avoid overflow
    // Max sum = 255*(3+5+7+7+5+3) = 255*30 = 7650 fits in 13 bits
    // Use 16 bits for safety before truncation
    wire [15:0] sum;
    
    integer i;
    
    // Register delay line and output
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line elements
            for (i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            delay_line[5] <= delay_line[4];
            delay_line[4] <= delay_line[3];
            delay_line[3] <= delay_line[2];
            delay_line[2] <= delay_line[1];
            delay_line[1] <= delay_line[0];
            delay_line[0] <= x;
            
            // Register the output
            y <= sum;
        end
    end
    
    // Compute sum of products (combinational)
    // Coefficients: [3, 5, 7, 7, 5, 3]
    // delay_line[0] is newest sample, delay_line[5] is oldest
    assign sum = (delay_line[0] * 8'd3) + 
                 (delay_line[1] * 8'd5) + 
                 (delay_line[2] * 8'd7) + 
                 (delay_line[3] * 8'd7) + 
                 (delay_line[4] * 8'd5) + 
                 (delay_line[5] * 8'd3);
    
endmodule