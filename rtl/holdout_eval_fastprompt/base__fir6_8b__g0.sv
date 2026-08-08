module base__fir6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] past_samples [0:5];
    reg [15:0] accumulator;

    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
            accumulator <= 0;
            for (int i = 0; i < 6; i = i + 1) begin
                past_samples[i] <= 0;
            end
        end else begin
            // shift all past samples
            past_samples[0] <= past_samples[1];
            past_samples[1] <= past_samples[2];
            past_samples[2] <= past_samples[3];
            past_samples[3] <= past_samples[4];
            past_samples[4] <= past_samples[5];
            past_samples[5] <= x;

            // calculate new accumulator
            accumulator <= (past_samples[0] * 3) + (past_samples[1] * 5) + (past_samples[2] * 7) + (past_samples[3] * 7) + (past_samples[4] * 5) + (past_samples[5] * 3);

            // output low 16 bits of accumulator
            y <= accumulator[15:0];
        end
    end

endmodule