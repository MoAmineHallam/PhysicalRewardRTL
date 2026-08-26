module mlp_s1__med21__g0 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] samples [0:20];
  reg [7:0] t0;
  reg [7:0] t1;
  reg [7:0] t2;
  reg [7:0] t3;
  reg [7:0] t4;
  reg [7:0] t5;
  reg [7:0] t6;
  reg [7:0] t7;
  reg [7:0] t8;
  reg [7:0] t9;
  reg [7:0] t10;
  reg [7:0] t11;
  reg [7:0] t12;
  reg [7:0] t13;
  reg [7:0] t14;
  reg [7:0] t15;
  reg [7:0] t16;
  reg [7:0] t17;
  reg [7:0] t18;
  reg [7:0] t19;
  reg [7:0] t20;
  integer i;
  integer j;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 21; i = i + 1) samples[i] <= 8'd0;
      y <= 16'd0;
    end else begin
      samples[0] <= x;
      for (i = 1; i < 21; i = i + 1) samples[i] <= samples[i-1];
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t0 = samples[i]; samples[i] = samples[j]; samples[j] = t0;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t1 = samples[i]; samples[i] = samples[j]; samples[j] = t1;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t2 = samples[i]; samples[i] = samples[j]; samples[j] = t2;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t3 = samples[i]; samples[i] = samples[j]; samples[j] = t3;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t4 = samples[i]; samples[i] = samples[j]; samples[j] = t4;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t5 = samples[i]; samples[i] = samples[j]; samples[j] = t5;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t6 = samples[i]; samples[i] = samples[j]; samples[j] = t6;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t7 = samples[i]; samples[i] = samples[j]; samples[j] = t7;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t8 = samples[i]; samples[i] = samples[j]; samples[j] = t8;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t9 = samples[i]; samples[i] = samples[j]; samples[j] = t9;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t10 = samples[i]; samples[i] = samples[j]; samples[j] = t10;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t11 = samples[i]; samples[i] = samples[j]; samples[j] = t11;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t12 = samples[i]; samples[i] = samples[j]; samples[j] = t12;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t13 = samples[i]; samples[i] = samples[j]; samples[j] = t13;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t14 = samples[i]; samples[i] = samples[j]; samples[j] = t14;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t15 = samples[i]; samples[i] = samples[j]; samples[j] = t15;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t16 = samples[i]; samples[i] = samples[j]; samples[j] = t16;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t17 = samples[i]; samples[i] = samples[j]; samples[j] = t17;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t18 = samples[i]; samples[i] = samples[j]; samples[j] = t18;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t19 = samples[i]; samples[i] = samples[j]; samples[j] = t19;
          end
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (samples[i] > samples[j]) begin
            t20 = samples[i]; samples[i] = samples[j]; samples[j] = t20;
          end
      y <= {8'd0, samples[10]};
    end
  end
endmodule
