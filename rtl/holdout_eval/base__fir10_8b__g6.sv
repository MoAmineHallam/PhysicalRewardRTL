module base__fir10_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

// Delay line and temporary signals
reg [7:0] delay_line[0:9];
reg [15:0] prod_sum;
reg [3:0] idx;

always @(posedge clk) begin
    // Reset logic
    if (!rst_n) begin
        y <= 0;
        prod_sum <= 0;
        idx <= 0;
        for (idx = 0; idx < 10; idx = idx + 1) begin
            delay_line[idx] <= 0;
        end
    end else begin
        // FIR calculation
        prod_sum <= (delay_line[0] * 3) + 
                    (delay_line[1] * 5) + 
                    (delay_line[2] * 7) + 
                    (delay_line[3] * 9) + 
                    (delay_line[4] * 11) + 
                    (delay_line[5] * 11) + 
                    (delay_line[6] * 9) + 
                    (delay_line[7] * 7) + 
                    (delay_line[8] * 5) + 
                    (delay_line[9] * 3);

        // Shift delay line
        for (idx = 9; idx > 0; idx = idx - 1) begin
            delay_line[idx] <= delay_line[idx - 1];
        end
        delay_line[0] <= x;

        // Output low 16 bits of sum of products
        y <= prod_sum;
    end
end

endmodule