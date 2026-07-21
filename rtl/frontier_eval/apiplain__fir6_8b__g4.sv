module apiplain__fir6_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line for 6 samples
    reg [7:0] delay_line [0:5];
    
    // Fixed coefficients
    localparam [3:0] COEFF0 = 3;
    localparam [3:0] COEFF1 = 5;
    localparam [3:0] COEFF2 = 7;
    localparam [3:0] COEFF3 = 7;
    localparam [3:0] COEFF4 = 5;
    localparam [3:0] COEFF5 = 3;
    
    // Intermediate product signals (use wider to avoid overflow before summing)
    wire [12:0] prod0, prod1, prod2, prod3, prod4, prod5;
    wire [15:0] sum;
    
    // Compute products
    assign prod0 = delay_line[0] * COEFF0;
    assign prod1 = delay_line[1] * COEFF1;
    assign prod2 = delay_line[2] * COEFF2;
    assign prod3 = delay_line[3] * COEFF3;
    assign prod4 = delay_line[4] * COEFF4;
    assign prod5 = delay_line[5] * COEFF5;
    
    // Sum all products
    assign sum = prod0 + prod1 + prod2 + prod3 + prod4 + prod5;
    
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line and output
            for (i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and load new sample
            delay_line[0] <= x;
            delay_line[1] <= delay_line[0];
            delay_line[2] <= delay_line[1];
            delay_line[3] <= delay_line[2];
            delay_line[4] <= delay_line[3];
            delay_line[5] <= delay_line[4];
            
            // Output the low 16 bits of the sum
            y <= sum[15:0];
        end
    end

endmodule