module base__firr18__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Define a 18-element array to store the taps
    reg [15:0] taps [0:17];
    
    // Define a 18-element array to store the delay line
    reg [7:0] delay_line [0:17];

    // Initialize the delay line to store the current input sample
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset the delay line to zero
            for (int i = 0; i < 18; i = i + 1)
                delay_line[i] <= 8'b0;
        end else begin
            // Shift the delay line left and insert the new input sample at the front
            for (int i = 17; i > 0; i = i - 1)
                delay_line[i] <= delay_line[i - 1];
            delay_line[0] <= x;
        end
    end

    // Compute the output using the delay line and coefficients
    always @(*) begin
        y = 16'd0;
        for (int k = 0; k < 18; k = k + 1) begin
            // Calculate the coefficient (k+1)
            taps[k] = k + 1;
            // Multiply the coefficient by the corresponding delayed sample and add to the output
            y = y + (taps[k] * delay_line[k]);
        end
    end

endmodule