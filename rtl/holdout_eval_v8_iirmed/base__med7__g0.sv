module base__med7__g0 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);

  // Number of samples to use for median calculation
  localparam NUM_SAMPLES = 7;

  // Shift register to hold the last NUM_SAMPLES samples
  reg [7:0] samples [0:NUM_SAMPLES-1];
  integer i;

  // Register to hold the median
  reg [7:0] median;

  // Clear all state when rst_n is low
  always @(negedge rst_n) begin
    for (i = 0; i < NUM_SAMPLES; i = i + 1) begin
      samples[i] <= 8'b0;
    end
    median <= 8'b0;
  end

  // Shift register to hold the last NUM_SAMPLES samples
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < NUM_SAMPLES; i = i + 1) begin
        samples[i] <= 8'b0;
      end
    end else begin
      for (i = NUM_SAMPLES-2; i >= 0; i = i - 1) begin
        samples[i+1] <= samples[i];
      end
      samples[0] <= x;
    end
  end

  // Calculate the median
  always @(posedge clk) begin
    if (!rst_n) begin
      median <= 8'b0;
    end else begin
      // Temporary variables to hold the sorted samples
      reg [7:0] sorted [0:NUM_SAMPLES-1];
      integer j, k;

      // Copy samples to sorted
      for (i = 0; i < NUM_SAMPLES; i = i + 1) begin
        sorted[i] <= samples[i];
      end

      // Sort samples
      for (i = 0; i < NUM_SAMPLES-1; i = i + 1) begin
        for (j = i+1; j < NUM_SAMPLES; j = j + 1) begin
          if (sorted[i] > sorted[j]) begin
            k = sorted[i];
            sorted[i] = sorted[j];
            sorted[j] = k;
          end
        end
      end

      // Median is the middle sample
      median <= sorted[NUM_SAMPLES/2];
    end
  end

  // Output the median
  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 16'b0;
    end else begin
      y <= {12'b0, median};
    end
  end

endmodule