module apiplain__firr10__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line for 10 taps (tap 0 = newest = current x)
    reg [7:0] delay_line [0:9];
    
    // Internal accumulator (wide enough to hold the sum without overflow)
    wire [15:0] sum;
    
    integer k;
    reg [15:0] acc;
    
    // Compute the sum: y = sum(k=0..9) (k+1) * tap[k]
    always @(*) begin
        acc = 16'd0;
        for (k = 0; k < 10; k = k + 1) begin
            acc = acc + (delay_line[k] * (k + 1));
        end
    end
    
    assign sum = acc;
    
    // Registered output and delay line update
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line values and output
            for (k = 0; k < 10; k = k + 1) begin
                delay_line[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample at tap 0
            delay_line[0] <= x;
            for (k = 1; k < 10; k = k + 1) begin
                delay_line[k] <= delay_line[k-1];
            end
            
            // Registered output
            y <= sum;
        end
    end

endmodule