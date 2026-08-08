module base__med7__g4(
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);

  reg [15:0] samples[6:0];
  integer i, j, k;
  reg [5:0] shift_cnt;
  reg [7:0] current_sample;

  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 7; i = i + 1) begin
        samples[i] <= 0;
      end
      y <= 0;
      shift_cnt <= 0;
      current_sample <= 0;
    end
    else begin
      current_sample <= x;
      // shift all samples one position to right
      for (i = 6; i >= 0; i = i - 1) begin
        samples[i+1] <= samples[i];
      end
      // insert current sample as first sample in array
      samples[0] <= {8'd0, current_sample};
      // sort samples
      for (i = 0; i < 7; i = i + 1) begin
        for (j = 0; j < 6; j = j + 1) begin
          if (samples[j] < samples[j+1]) begin
            k = samples[j+1];
            samples[j+1] = samples[j];
            samples[j] = k;
          end
        end
      end
      // output median
      y <= samples[3];
      // shift shift_cnt one position to right
      shift_cnt <= {shift_cnt[4:0], 1'b0};
      // clear samples if shift_cnt is one
      if (shift_cnt == 1) begin
        for (i = 0; i < 7; i = i + 1) begin
          samples[i] <= 0;
        end
      end
    end
  end

endmodule