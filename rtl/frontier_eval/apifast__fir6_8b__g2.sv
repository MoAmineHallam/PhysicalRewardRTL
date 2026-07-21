module apifast__fir6_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line registers (6 taps)
    reg [7:0] d0, d1, d2, d3, d4, d5;
    
    // Pipeline registers for multiplication results
    reg [15:0] m0, m1, m2, m3, m4, m5;
    
    // Pipeline registers for partial sums
    reg [16:0] s0, s1; // extra bit for carry
    
    // Stage 1: Shift delay line and compute products
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            d0 <= 8'd0;
            d1 <= 8'd0;
            d2 <= 8'd0;
            d3 <= 8'd0;
            d4 <= 8'd0;
            d5 <= 8'd0;
            
            m0 <= 16'd0;
            m1 <= 16'd0;
            m2 <= 16'd0;
            m3 <= 16'd0;
            m4 <= 16'd0;
            m5 <= 16'd0;
        end else begin
            // Shift delay line
            d5 <= d4;
            d4 <= d3;
            d3 <= d2;
            d2 <= d1;
            d1 <= d0;
            d0 <= x;
            
            // Compute products with fixed coefficients
            // Coefficients: [3,5,7,7,5,3]
            m0 <= d0 * 8'd3;  // newest sample * 3
            m1 <= d1 * 8'd5; 
            m2 <= d2 * 8'd7;
            m3 <= d3 * 8'd7;
            m4 <= d4 * 8'd5;
            m5 <= d5 * 8'd3;  // oldest sample * 3
        end
    end
    
    // Stage 2: First level of addition (3+3 structure)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s0 <= 17'd0;
            s1 <= 17'd0;
        end else begin
            s0 <= {1'b0, m0} + {1'b0, m1} + {1'b0, m2}; // sum first 3 products
            s1 <= {1'b0, m3} + {1'b0, m4} + {1'b0, m5}; // sum last 3 products
        end
    end
    
    // Stage 3: Final addition and output
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'd0;
        end else begin
            y <= (s0 + s1); // final sum, low 16 bits automatically
        end
    end
    
endmodule