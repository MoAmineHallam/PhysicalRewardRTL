module apiplain__fir6_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line for 6 taps
    reg [7:0] delay_line [0:5];
    integer i;

    // Product and sum (wide enough to avoid overflow before truncation)
    wire [15:0] prod [0:5];
    wire [18:0] sum;

    // Fixed coefficients: [3, 5, 7, 7, 5, 3]
    assign prod[0] = delay_line[0] * 3;
    assign prod[1] = delay_line[1] * 5;
    assign prod[2] = delay_line[2] * 7;
    assign prod[3] = delay_line[3] * 7;
    assign prod[4] = delay_line[4] * 5;
    assign prod[5] = delay_line[5] * 3;

    assign sum = prod[0] + prod[1] + prod[2] + prod[3] + prod[4] + prod[5];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line and output
            for (i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            delay_line[0] <= x;
            for (i = 1; i < 6; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            // Output the low 16 bits of the sum
            y <= sum[15:0];
        end
    end

endmodule