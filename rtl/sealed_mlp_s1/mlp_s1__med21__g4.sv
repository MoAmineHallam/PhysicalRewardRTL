module mlp_s1__med21__g4 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] samples [0:20];
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
  reg [7:0] tmp10;
  reg [7:0] tmp11;
  reg [7:0] tmp12;
  reg [7:0] tmp13;
  reg [7:0] tmp14;
  reg [7:0] tmp15;
  reg [7:0] tmp16;
  reg [7:0] tmp17;
  reg [7:0] tmp18;
  reg [7:0] tmp19;
  reg [7:0] sorted [0:20];
  integer i, j, k;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 21; i = i + 1) begin
        samples[i] <= 8'd0;
      end
      y <= 16'd0;
    end else begin
      samples[0] <= x;
      for (i = 1; i < 21; i = i + 1) begin
        samples[i] <= samples[i-1];
      end
      for (i = 0; i < 21; i = i + 1) begin
        sorted[i] = samples[i];
      end
      for (i = 0; i < 20; i = i + 1) begin
        for (j = i + 1; j < 21; j = j + 1) begin
          if (sorted[i] > sorted[j]) begin
            tmp0 = sorted[i];
            sorted[i] = sorted[j];
            sorted[j] = tmp0;
          end
        end
      end
      y <= {8'b0, sorted[10]};
    end
  end
endmodule
