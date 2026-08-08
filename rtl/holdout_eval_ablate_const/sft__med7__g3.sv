module sft__med7__g3 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] samples [0:6];
  reg [7:0] sorted [0:6];
  reg [7:0] t;
  integer i, j;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 7; i = i + 1) begin
        samples[i] <= 8'd0;
        sorted[i] <= 8'd0;
      end
      y <= 16'd0;
    end else begin
      samples[0] <= x;
      for (i = 1; i < 7; i = i + 1) samples[i] <= samples[i-1];
      for (i = 0; i < 7; i = i + 1) sorted[i] <= samples[i];
      for (i = 0; i < 6; i = i + 1)
        for (j = 0; j < 6 - i; j = j + 1)
          if (sorted[j] > sorted[j+1]) begin
            t = sorted[j]; sorted[j] = sorted[j+1]; sorted[j+1] = t;
          end
      y <= {8'b0, sorted[3]};
    end
  end
endmodule