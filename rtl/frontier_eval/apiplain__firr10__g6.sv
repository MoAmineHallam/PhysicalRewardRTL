module apiplain__firr10__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:9]; // 10-element delay line, tap0 = newest sample
    integer k;
    reg [15:0] sum;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all delay line elements
            for (k = 0; k < 10; k = k + 1) begin
                delay_line[k] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            for (k = 9; k > 0; k = k - 1) begin
                delay_line[k] <= delay_line[k-1];
            end
            delay_line[0] <= x;

            // Compute sum of (k+1) * tap[k]
            sum = 16'd0;
            for (k = 0; k < 10; k = k + 1) begin
                sum = sum + ((k + 1) * delay_line[k]);
            end

            // Output low 16 bits of the sum
            y <= sum;
        end
    end

endmodule