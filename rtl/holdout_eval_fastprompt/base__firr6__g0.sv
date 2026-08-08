module base__firr6__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap [0:5];
    reg [15:0] sum [0:5];

    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
            for (int i = 0; i < 6; i = i + 1) begin
                tap[i] <= 0;
                sum[i] <= 0;
            end
        end else begin
            // Update delay line
            for (int i = 4; i >= 0; i = i - 1) begin
                tap[i+1] <= tap[i];
            end
            tap[0] <= x;

            // Compute sum
            for (int i = 0; i < 6; i = i + 1) begin
                sum[i] <= (i+1) * tap[i];
            end

            // Add all sums
            y <= sum[0] + sum[1] + sum[2] + sum[3] + sum[4] + sum[5];
        end
    end

endmodule