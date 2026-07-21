module apiplain__fir10_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line of 10 past samples
    reg [7:0] delay_line [0:9];
    integer i;

    // Sum of products (wide enough to avoid overflow before truncation)
    wire [15:0] sum_prod;

    assign sum_prod = 
        (delay_line[0] * 3)  +
        (delay_line[1] * 5)  +
        (delay_line[2] * 7)  +
        (delay_line[3] * 9)  +
        (delay_line[4] * 11) +
        (delay_line[5] * 11) +
        (delay_line[6] * 9)  +
        (delay_line[7] * 7)  +
        (delay_line[8] * 5)  +
        (delay_line[9] * 3);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1)
                delay_line[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            // Shift delay line and insert new sample
            delay_line[0] <= x;
            for (i = 1; i < 10; i = i + 1)
                delay_line[i] <= delay_line[i-1];

            // Output low 16 bits of the sum of products
            y <= sum_prod[15:0];
        end
    end

endmodule