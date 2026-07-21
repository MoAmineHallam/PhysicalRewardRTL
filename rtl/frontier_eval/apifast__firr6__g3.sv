module apifast__firr6__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line registers (6 taps)
    reg [7:0] tap0, tap1, tap2, tap3, tap4, tap5;
    
    // Pipeline registers for partial products and sums
    // Stage 1: Multiply each tap by coefficient
    reg [15:0] prod0, prod1, prod2, prod3, prod4, prod5;
    // Stage 2: First level of addition tree
    reg [15:0] sum01, sum23, sum45;
    // Stage 3: Second level of addition tree  
    reg [15:0] sum0123, sum45_reg;
    // Stage 4: Final sum and output
    reg [15:0] sum_total;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tap0 <= 8'd0;
            tap1 <= 8'd0;
            tap2 <= 8'd0;
            tap3 <= 8'd0;
            tap4 <= 8'd0;
            tap5 <= 8'd0;
            
            prod0 <= 16'd0;
            prod1 <= 16'd0;
            prod2 <= 16'd0;
            prod3 <= 16'd0;
            prod4 <= 16'd0;
            prod5 <= 16'd0;
            
            sum01 <= 16'd0;
            sum23 <= 16'd0;
            sum45 <= 16'd0;
            
            sum0123 <= 16'd0;
            sum45_reg <= 16'd0;
            
            sum_total <= 16'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            tap5 <= tap4;
            tap4 <= tap3;
            tap3 <= tap2;
            tap2 <= tap1;
            tap1 <= tap0;
            tap0 <= x;
            
            // Stage 1: Multiply each tap by coefficient (k+1)
            // Coefficients: tap0*1, tap1*2, tap2*3, tap3*4, tap4*5, tap5*6
            prod0 <= {8'd0, tap0};  // *1 - just zero-extend
            prod1 <= {tap1, 1'd0} + {8'd0, tap1};  // *2 = shift left 1 + zero
            // Actually simpler: *2 = {tap1, 1'b0} with correct width
            // But we need 16-bit results; let's be explicit:
            prod1 <= tap1 * 16'd2;
            prod2 <= tap2 * 16'd3;
            prod3 <= tap3 * 16'd4;
            prod4 <= tap4 * 16'd5;
            prod5 <= tap5 * 16'd6;
            
            // Stage 2: First adder tree level - pair sums
            sum01 <= prod0 + prod1;
            sum23 <= prod2 + prod3;
            sum45 <= prod4 + prod5;
            
            // Stage 3: Second adder tree level
            sum0123 <= sum01 + sum23;
            sum45_reg <= sum45;
            
            // Stage 4: Final sum and output
            sum_total <= sum0123 + sum45_reg;
            y <= sum_total;
        end
    end

endmodule