module base__fir6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line of past samples
    reg [7:0] sample_delay_line [5:0];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'd0;
            for (int i = 0; i < 6; i = i + 1) begin
                sample_delay_line[i] <= 0;
            end
        end
        else begin
            sample_delay_line[0] <= x;
            for (int i = 1; i < 6; i = i + 1) begin
                sample_delay_line[i] <= sample_delay_line[i-1];
            end

            // Calculate the sum of products
            y <= sample_delay_line[5]*3 +
                 sample_delay_line[4]*5 +
                 sample_delay_line[3]*7 +
                 sample_delay_line[2]*7 +
                 sample_delay_line[1]*5 +
                 sample_delay_line[0]*3;
        end
    end

endmodule