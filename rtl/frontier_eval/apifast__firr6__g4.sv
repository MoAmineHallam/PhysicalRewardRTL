module apifast__firr6__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 6-element delay line (tap 0 = newest)
    reg [7:0] tap0, tap1, tap2, tap3, tap4, tap5;
    
    // Pipeline registers for partial products and sums
    reg [15:0] p0, p1, p2, p3, p4, p5;  // (k+1)*tap[k]
    reg [15:0] s0, s1, s2, s3, s4;      // partial sums

    // Stage 1: Shift delay line and compute products
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tap0 <= 8'd0;
            tap1 <= 8'd0;
            tap2 <= 8'd0;
            tap3 <= 8'd0;
            tap4 <= 8'd0;
            tap5 <= 8'd0;
            p0 <= 16'd0;
            p1 <= 16'd0;
            p2 <= 16'd0;
            p3 <= 16'd0;
            p4 <= 16'd0;
            p5 <= 16'd0;
        end else begin
            // Shift samples: new x becomes tap0, rest shift right
            tap0 <= x;
            tap1 <= tap0;
            tap2 <= tap1;
            tap3 <= tap2;
            tap4 <= tap3;
            tap5 <= tap4;
            
            // Compute all products in parallel (coefficient = k+1)
            p0 <= {8'd0, tap0} * 16'd1;     // 1 * tap0
            p1 <= {8'd0, tap1} * 16'd2;     // 2 * tap1
            p2 <= {8'd0, tap2} * 16'd3;     // 3 * tap2
            p3 <= {8'd0, tap3} * 16'd4;     // 4 * tap3
            p4 <= {8'd0, tap4} * 16'd5;     // 5 * tap4
            p5 <= {8'd0, tap5} * 16'd6;     // 6 * tap5
        end
    end

    // Stage 2: First-level addition tree (3 adders)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s0 <= 16'd0;
            s1 <= 16'd0;
            s2 <= 16'd0;
        end else begin
            s0 <= p0 + p1;   // sum of first 2 products
            s1 <= p2 + p3;   // sum of next 2 products
            s2 <= p4 + p5;   // sum of last 2 products
        end
    end

    // Stage 3: Second-level addition (2 adders)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s3 <= 16'd0;
            s4 <= 16'd0;
        end else begin
            s3 <= s0 + s1;
            s4 <= s2;        // just pass through
        end
    end

    // Stage 4: Final addition and output
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'd0;
        end else begin
            y <= s3 + s4;    // final sum, automatically low 16 bits
        end
    end

endmodule