module apifast__firr6__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line registers (6 taps: tap0 = newest, tap5 = oldest)
    reg [7:0] tap0, tap1, tap2, tap3, tap4, tap5;

    // Pipeline registers for partial products (first multiply stage)
    reg [15:0] prod0, prod1, prod2, prod3, prod4, prod5;

    // Pipeline registers for tree adder (intermediate sums)
    reg [15:0] sum0, sum1, sum2, sum3, sum4;

    // Output register y is already declared as reg [15:0] y

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all state
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

            sum0 <= 16'd0;
            sum1 <= 16'd0;
            sum2 <= 16'd0;
            sum3 <= 16'd0;
            sum4 <= 16'd0;

            y    <= 16'd0;
        end else begin
            // Stage 1: Shift delay line (tap0 gets new sample x)
            tap0 <= x;
            tap1 <= tap0;
            tap2 <= tap1;
            tap3 <= tap2;
            tap4 <= tap3;
            tap5 <= tap4;

            // Stage 2: Multiply each tap by coefficient (k+1) — coefficients are 1,2,3,4,5,6
            // Note: (k+1)*tap[k] where tap values are 8-bit unsigned, product fits in 16 bits
            prod0 <= {8'd0, tap0} * 16'd1;   // 1 * tap0
            prod1 <= {8'd0, tap1} * 16'd2;   // 2 * tap1
            prod2 <= {8'd0, tap2} * 16'd3;   // 3 * tap2
            prod3 <= {8'd0, tap3} * 16'd4;   // 4 * tap3
            prod4 <= {8'd0, tap4} * 16'd5;   // 5 * tap4
            prod5 <= {8'd0, tap5} * 16'd6;   // 6 * tap5

            // Stage 3: First level of adder tree (pairwise sums)
            sum0 <= prod0 + prod1;
            sum1 <= prod2 + prod3;
            sum2 <= prod4 + prod5;

            // Stage 4: Second level of adder tree
            sum3 <= sum0 + sum1;
            sum4 <= sum2;  // just pass through

            // Stage 5: Final sum and output
            y <= sum3 + sum4;
        end
    end

endmodule