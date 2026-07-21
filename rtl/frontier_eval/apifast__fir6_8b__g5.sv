module apifast__fir6_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line registers (pipeline stage 1)
    reg [7:0] d0, d1, d2, d3, d4, d5;
    
    // Stage 1 products (pipeline stage 2)
    reg [11:0] p0, p1, p2, p3, p4, p5;
    
    // Stage 2 partial sums (pipeline stage 3)
    reg [13:0] sum01, sum23, sum45;
    
    // Stage 3 intermediate sum (pipeline stage 4)
    reg [15:0] sum0123, sum45_ext;
    
    // Stage 4 final sum (pipeline stage 5 - output)
    reg [15:0] y_next;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all registers
            d0 <= 8'd0;
            d1 <= 8'd0;
            d2 <= 8'd0;
            d3 <= 8'd0;
            d4 <= 8'd0;
            d5 <= 8'd0;
            
            p0 <= 12'd0;
            p1 <= 12'd0;
            p2 <= 12'd0;
            p3 <= 12'd0;
            p4 <= 12'd0;
            p5 <= 12'd0;
            
            sum01 <= 14'd0;
            sum23 <= 14'd0;
            sum45 <= 14'd0;
            
            sum0123 <= 16'd0;
            sum45_ext <= 16'd0;
            
            y <= 16'd0;
        end else begin
            // Stage 1: Shift delay line and load new sample
            d0 <= x;
            d1 <= d0;
            d2 <= d1;
            d3 <= d2;
            d4 <= d3;
            d5 <= d4;
            
            // Stage 2: Multiply each sample by coefficient
            // Coefficients: [3, 5, 7, 7, 5, 3]
            p0 <= {4'd0, d0} + {4'd0, d0, 1'b0};                    // ×3 = ×2 + ×1
            p1 <= {4'd0, d1, 2'b0} + {4'd0, d1};                     // ×5 = ×4 + ×1
            p2 <= {4'd0, d2, 3'b0} - {4'd0, d2};                     // ×7 = ×8 - ×1
            p3 <= {4'd0, d3, 3'b0} - {4'd0, d3};                     // ×7 = ×8 - ×1
            p4 <= {4'd0, d4, 2'b0} + {4'd0, d4};                     // ×5 = ×4 + ×1
            p5 <= {4'd0, d5} + {4'd0, d5, 1'b0};                    // ×3 = ×2 + ×1
            
            // Stage 3: Pairwise sums
            sum01 <= {2'b0, p0} + {2'b0, p1};
            sum23 <= {2'b0, p2} + {2'b0, p3};
            sum45 <= {2'b0, p4} + {2'b0, p5};
            
            // Stage 4: Combine pairs
            sum0123 <= {2'b0, sum01} + {2'b0, sum23};
            sum45_ext <= {2'b0, sum45};
            
            // Stage 5: Final sum and output (take low 16 bits)
            y <= sum0123 + sum45_ext;
        end
    end

endmodule