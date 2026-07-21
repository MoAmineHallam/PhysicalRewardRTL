module apifast__fir6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line registers (6 taps)
    reg [7:0] d0, d1, d2, d3, d4, d5;
    
    // Stage 1: Multiplications (all done in parallel)
    reg [15:0] m0, m1, m2, m3, m4, m5;  // 3*8=12 bits max, use 16 for safety
    
    // Stage 2: First level of additions (3 parallel additions)
    reg [16:0] s0, s1, s2;  // 16+1 bit to handle carry
    
    // Stage 3: Second level of additions
    reg [17:0] t0, t1;      // 17+1 bit
    
    // Stage 4: Final addition
    reg [18:0] final_sum;   // 18+1 bit
    
    // Pipeline control signals
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all registers
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
            
            s0 <= 17'd0;
            s1 <= 17'd0;
            s2 <= 17'd0;
            
            t0 <= 18'd0;
            t1 <= 18'd0;
            
            final_sum <= 19'd0;
            y <= 16'd0;
        end else begin
            // Stage 0: Shift delay line and capture input
            d0 <= x;
            d1 <= d0;
            d2 <= d1;
            d3 <= d2;
            d4 <= d3;
            d5 <= d4;
            
            // Stage 1: Multiplications (coefficients [3,5,7,7,5,3])
            m0 <= {4'd0, d0} + {4'd0, d0} + {4'd0, d0};                    // x * 3
            m1 <= {3'd0, d1, 2'd0} + {4'd0, d1};                           // x * 5
            m2 <= {d2, 3'd0} - d2;                                          // x * 7
            m3 <= {d3, 3'd0} - d3;                                          // x * 7
            m4 <= {3'd0, d4, 2'd0} + {4'd0, d4};                           // x * 5
            m5 <= {4'd0, d5} + {4'd0, d5} + {4'd0, d5};                    // x * 3
            
            // Stage 2: First addition level (3 parallel adds)
            s0 <= {1'b0, m0} + {1'b0, m1};
            s1 <= {1'b0, m2} + {1'b0, m3};
            s2 <= {1'b0, m4} + {1'b0, m5};
            
            // Stage 3: Second addition level
            t0 <= {1'b0, s0} + {1'b0, s1};
            t1 <= {1'b0, s2};
            
            // Stage 4: Final addition and output
            final_sum <= {1'b0, t0} + {1'b0, t1};
            y <= final_sum[15:0];
        end
    end

endmodule