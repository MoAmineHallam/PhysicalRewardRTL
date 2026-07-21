module apiplain__fir6_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Fixed coefficients [3, 5, 7, 7, 5, 3]
    // 6-tap delay line for past samples
    reg [7:0] delay_line [0:5];
    
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line elements and output
            for (i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            y <= 16'd0;
        end
        else begin
            // Shift delay line and insert new sample
            delay_line[0] <= x;      // newest sample (h0)
            delay_line[1] <= delay_line[0];
            delay_line[2] <= delay_line[1];
            delay_line[3] <= delay_line[2];
            delay_line[4] <= delay_line[3];
            delay_line[5] <= delay_line[4];  // oldest sample (h5)
            
            // Compute sum of products and take low 16 bits
            // y = 3*x[n] + 5*x[n-1] + 7*x[n-2] + 7*x[n-3] + 5*x[n-4] + 3*x[n-5]
            y <= (delay_line[0] * 8'd3) +
                 (delay_line[1] * 8'd5) +
                 (delay_line[2] * 8'd7) +
                 (delay_line[3] * 8'd7) +
                 (delay_line[4] * 8'd5) +
                 (delay_line[5] * 8'd3);
        end
    end

endmodule