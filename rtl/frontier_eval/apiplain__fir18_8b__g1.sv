module apiplain__fir18_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 18-element delay line (registered)
    reg [7:0] delay_line [0:17];
    
    // Fixed coefficients
    wire [4:0] coeff [0:17];
    assign coeff[0]  = 5'd3;
    assign coeff[1]  = 5'd5;
    assign coeff[2]  = 5'd7;
    assign coeff[3]  = 5'd9;
    assign coeff[4]  = 5'd11;
    assign coeff[5]  = 5'd13;
    assign coeff[6]  = 5'd15;
    assign coeff[7]  = 5'd17;
    assign coeff[8]  = 5'd19;
    assign coeff[9]  = 5'd19;
    assign coeff[10] = 5'd17;
    assign coeff[11] = 5'd15;
    assign coeff[12] = 5'd13;
    assign coeff[13] = 5'd11;
    assign coeff[14] = 5'd9;
    assign coeff[15] = 5'd7;
    assign coeff[16] = 5'd5;
    assign coeff[17] = 5'd3;
    
    // Intermediate product and sum signals
    integer i;
    reg [12:0] product [0:17];  // 8-bit * 5-bit = 13 bits max
    reg [20:0] sum;             // Sum of 18 products: 13 + log2(18) ≈ 17.17 → 18 bits, use 21 for safety
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line
            for (i = 0; i < 18; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            delay_line[0] <= x;
            for (i = 1; i < 18; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            
            // Compute products
            for (i = 0; i < 18; i = i + 1) begin
                product[i] = delay_line[i] * coeff[i];
            end
            
            // Sum all products
            sum = 21'd0;
            for (i = 0; i < 18; i = i + 1) begin
                sum = sum + product[i];
            end
            
            // Output low 16 bits
            y <= sum[15:0];
        end
    end

endmodule