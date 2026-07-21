module apifast__firr6__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line registers (tap 0 = newest)
    reg [7:0] tap0, tap1, tap2, tap3, tap4, tap5;
    
    // Pipeline registers for partial sums
    reg [15:0] psum1, psum2, psum3, psum4;
    reg [15:0] psum5_final;
    
    // Coefficient multiplication results (pipelined)
    reg [15:0] m0, m1, m2, m3, m4, m5;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all state
            tap0 <= 8'd0;
            tap1 <= 8'd0;
            tap2 <= 8'd0;
            tap3 <= 8'd0;
            tap4 <= 8'd0;
            tap5 <= 8'd0;
            
            m0 <= 16'd0;
            m1 <= 16'd0;
            m2 <= 16'd0;
            m3 <= 16'd0;
            m4 <= 16'd0;
            m5 <= 16'd0;
            
            psum1 <= 16'd0;
            psum2 <= 16'd0;
            psum3 <= 16'd0;
            psum4 <= 16'd0;
            psum5_final <= 16'd0;
            
            y <= 16'd0;
        end else begin
            // Stage 1: Shift delay line and load new sample, compute multiplications
            tap0 <= x;
            tap1 <= tap0;
            tap2 <= tap1;
            tap3 <= tap2;
            tap4 <= tap3;
            tap5 <= tap4;
            
            // Coefficients k+1: 1,2,3,4,5,6
            m0 <= x * 8'd1;           // tap0 * 1
            m1 <= tap0 * 8'd2;        // tap1 * 2
            m2 <= tap1 * 8'd3;        // tap2 * 3
            m3 <= tap2 * 8'd4;        // tap3 * 4
            m4 <= tap3 * 8'd5;        // tap4 * 5
            m5 <= tap4 * 8'd6;        // tap5 * 6 (using tap4 before shift)
            
            // Stage 2: First level of additions (2 + 2 + 2)
            psum1 <= m0 + m1;
            psum2 <= m2 + m3;
            psum3 <= m4 + m5;
            
            // Stage 3: Second level (psum1+psum2) and psum3 propagated
            psum4 <= psum1 + psum2;
            psum5_final <= psum3;  // just propagate
            
            // Stage 4: Final addition and output
            y <= psum4 + psum5_final;
        end
    end

endmodule