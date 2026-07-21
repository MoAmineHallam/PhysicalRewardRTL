module apiplain__fir6_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line for past 6 samples
    reg [7:0] delay_line [0:5];
    
    // Fixed coefficients
    localparam [3:0] coeff0 = 3;
    localparam [3:0] coeff1 = 5;
    localparam [3:0] coeff2 = 7;
    localparam [3:0] coeff3 = 7;
    localparam [3:0] coeff4 = 5;
    localparam [3:0] coeff5 = 3;
    
    // Product terms - each is up to 12 bits (8-bit sample × 4-bit coeff)
    wire [11:0] prod0, prod1, prod2, prod3, prod4, prod5;
    
    assign prod0 = delay_line[0] * coeff0;
    assign prod1 = delay_line[1] * coeff1;
    assign prod2 = delay_line[2] * coeff2;
    assign prod3 = delay_line[3] * coeff3;
    assign prod4 = delay_line[4] * coeff4;
    assign prod5 = delay_line[5] * coeff5;
    
    // Sum of products - up to 14 bits (6 terms × 12 bits max)
    wire [13:0] sum;
    assign sum = prod0 + prod1 + prod2 + prod3 + prod4 + prod5;
    
    // Sequential logic
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line and output
            for (i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and input new sample
            delay_line[0] <= x;
            for (i = 1; i < 6; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            
            // Output low 16 bits of sum
            y <= {2'b0, sum};  // Zero-extend to 16 bits (since sum is only 14 bits)
        end
    end

endmodule