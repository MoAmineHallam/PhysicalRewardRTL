module base__med7__g1 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);

  reg [7:0] samples [6:0];
  reg [3:0] i, j, min_index;
  reg [7:0] temp;
  reg [15:0] min_value;

  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 7; i = i + 1) begin
        samples[i] <= 8'd0;
      end
      y <= 16'd0;
    end else begin
      // Shift samples array
      for (i = 6; i > 0; i = i - 1) begin
        samples[i] <= samples[i-1];
      end
      samples[0] <= x;

      // Find median using bubble sort
      for (i = 0; i < 7; i = i + 1) begin
        min_index = i;
        min_value = {16'd0, samples[i]};
        for (j = i + 1; j < 7; j = j + 1) begin
          if (samples[j] < min_value) begin
            min_index = j;
            min_value = {16'd0, samples[j]};
          end
        end
        temp = samples[i];
        samples[i] = samples[min_index];
        samples[min_index] = temp;
      end

      // Zero-extend median to 16 bits
      y <= {16'd0, samples[3]};
    end
  end

endmodule