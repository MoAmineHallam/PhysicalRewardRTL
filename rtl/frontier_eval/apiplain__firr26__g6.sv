module apiplain__firr26__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 26-element delay line (tap 0 = newest sample)
    reg [7:0] delay_line [0:25];
    
    // Internal wires for the multiply-accumulate operations
    wire [23:0] sum_result;
    
    integer k;
    reg [23:0] sum;
    reg [23:0] term;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line and output
            for (k = 0; k < 26; k = k + 1) begin
                delay_line[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            for (k = 25; k > 0; k = k - 1) begin
                delay_line[k] <= delay_line[k-1];
            end
            delay_line[0] <= x;
            
            // Compute FIR sum
            sum = 24'd0;
            for (k = 0; k < 26; k = k + 1) begin
                term = (k + 1) * delay_line[k];
                sum = sum + term;
            end
            
            // Take lower 16 bits
            y <= sum[15:0];
        end
    end
    
endmodule