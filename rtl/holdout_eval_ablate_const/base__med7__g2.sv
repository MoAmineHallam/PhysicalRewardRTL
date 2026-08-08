module base__med7__g2 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);

  reg [7:0] samples [0:6];
  int i, j, min_idx;
  reg [15:0] temp;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      for (i = 0; i < 7; i = i + 1) begin
        samples[i] <= 8'b0;
      end
      y <= 16'b0;
    end
    else begin
      // Shift samples
      for (i = 6; i > 0; i = i - 1) begin
        samples[i] <= samples[i-1];
      end

      // Add current sample
      samples[0] <= x;

      // Sort samples
      for (i = 0; i < 7; i = i + 1) begin
        min_idx = i;
        for (j = i+1; j < 7; j = j + 1) begin
          if (samples[j] < samples[min_idx]) begin
            min_idx = j;
          end
        end
        temp = samples[i];
        samples[i] = samples[min_idx];
        samples[min_idx] = temp;
      end

      // Output median
      y <= {16'b0, samples[3]};
    end
  end

endmodule