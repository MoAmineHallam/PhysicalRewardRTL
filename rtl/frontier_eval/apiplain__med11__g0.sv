module apiplain__med11__g0 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);

  // Shift register to hold 11 samples (including current)
  reg [7:0] samples [0:10];
  integer i, j, k;
  
  // Sort array for median calculation
  reg [7:0] sorted [0:10];
  reg [7:0] temp;
  
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      // Clear shift register
      for (i = 0; i < 11; i = i + 1)
        samples[i] <= 8'd0;
      y <= 16'd0;
    end else begin
      // Shift in new sample (shift-right operation)
      for (i = 0; i < 10; i = i + 1)
        samples[i] <= samples[i+1];
      samples[10] <= x;
      
      // Copy to sorting array
      for (j = 0; j < 11; j = j + 1)
        sorted[j] = samples[j];
      
      // Bubble sort - find median (6th element after sorting)
      for (j = 0; j < 11; j = j + 1) begin
        for (k = 0; k < 10 - j; k = k + 1) begin
          if (sorted[k] > sorted[k+1]) begin
            temp = sorted[k];
            sorted[k] = sorted[k+1];
            sorted[k+1] = temp;
          end
        end
      end
      
      // Output median (index 5 is 6th element in 0-based array)
      y <= {8'd0, sorted[5]};
    end
  end

endmodule