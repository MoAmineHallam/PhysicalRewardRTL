module base__med7__g0 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);

  reg [15:0] samples[6:0]; // 7-sample window
  integer i;
  integer j;
  reg [7:0] tmp;

  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 16'b0;
      for (i = 0; i < 7; i = i + 1) begin
        samples[i] <= 16'b0;
      end
    end else begin
      // Shift samples
      for (i = 6; i > 0; i = i - 1) begin
        samples[i] <= samples[i - 1];
      end
      
      // Add new sample
      samples[0] <= {8'b0, x};
      
      // Sort samples
      for (i = 0; i < 7; i = i + 1) begin
        for (j = i+1; j < 7; j = j + 1) begin
          if (samples[i] > samples[j]) begin
            tmp = samples[i];
            samples[i] = samples[j];
            samples[j] = tmp;
          end
        end
      end
      
      // Output median
      y <= samples[3];
    end
  end

endmodule