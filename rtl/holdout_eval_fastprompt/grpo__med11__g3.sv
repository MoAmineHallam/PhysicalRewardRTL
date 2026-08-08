module grpo__med11__g3 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] samples [0:10];
  reg [7:0] tmp0;
  reg [7:0] tmp1;
  reg [7:0] tmp2;
  reg [7:0] tmp3;
  reg [7:0] tmp4;
  reg [7:0] tmp5;
  reg [7:0] tmp6;
  reg [7:0] tmp7;
  reg [7:0] tmp8;
  reg [7:0] tmp9;
  reg [7:0] sorted [0:10];
  reg [7:0] med;
  integer i, j, k;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 11; i = i + 1) samples[i] <= 8'd0;
      y<=16'd0;
    end else begin
      samples[0] <= x;
      for (i = 1; i < 11; i = i + 1) samples[i] <= samples[i-1];
      tmp0 = samples[0];
      tmp1 = samples[1];
      tmp2 = samples[2];
      tmp3 = samples[3];
      tmp4 = samples[4];
      tmp5 = samples[5];
      tmp6 = samples[6];
      tmp7 = samples[7];
      tmp8 = samples[8];
      tmp9 = samples[9];
      sorted[0] = tmp0;
      sorted[1] = tmp1;
      sorted[2] = tmp2;
      sorted[3] = tmp3;
      sorted[4] = tmp4;
      sorted[5] = tmp5;
      sorted[6] = tmp6;
      sorted[7] = tmp7;
      sorted[8] = tmp8;
      sorted[9] = tmp9;
      sorted[10] = x;
      for (i = 0; i < 10; i = i + 1)
        for (j = i + 1; j < 11; j = j + 1)
          if (sorted[i] > sorted[j]) begin med = sorted[i]; sorted[i] = sorted[j]; sorted[j] = med; end
      y <= {8'd0, sorted[5]};
    end
  end
endmodule