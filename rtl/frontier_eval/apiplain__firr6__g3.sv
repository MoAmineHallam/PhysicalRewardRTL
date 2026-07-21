module apiplain__firr6__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 6-element delay line (tap 0 = newest = current x)
    reg [7:0] tap [0:5];
    
    // Accumulator for sum of products (wide enough to hold full sum)
    wire [15:0] sum;
    
    integer k;
    reg [15:0] sum_reg;
    
    // Compute the sum of (k+1)*tap[k]
    always @(*) begin
        sum_reg = 0;
        for (k = 0; k < 6; k = k + 1) begin
            sum_reg = sum_reg + ((k + 1) * tap[k]);
        end
    end
    
    assign sum = sum_reg[15:0];
    
    // Register the output and update the delay line
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'd0;
            for (k = 0; k < 6; k = k + 1) begin
                tap[k] <= 8'd0;
            end
        end else begin
            // Shift delay line and insert new sample
            tap[5] <= tap[4];
            tap[4] <= tap[3];
            tap[3] <= tap[2];
            tap[2] <= tap[1];
            tap[1] <= tap[0];
            tap[0] <= x;
            
            // Register output
            y <= sum;
        end
    end

endmodule