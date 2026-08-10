module grpo__med7__g5 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] window [0:6];
  reg [7:0] tmp0;
  reg [7:0] tmp1;
  reg [7:0] tmp2;
  reg [7:0] tmp3;
  reg [7:0] tmp4;
  reg [7:0] tmp5;
  integer i, j, k;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 7; i = i + 1) window[i] <= 8'd0;
      y <= 16'd0;
    end else begin
      window[0] <= x;
      for (i = 1; i < 7; i = i + 1) window[i] <= window[i-1];
      for (i = 0; i < 6; i = i + 1)
        for (j = i + 1; j < 7; j = j + 1)
          if (window[i] > window[j]) begin tmp0 = window[i]; window[i] = window[j]; window[j] = tmp0; end
      for (i = 0; i < 5; i = i + 1)
        for (j = i + 1; j < 6; j = j + 1)
          if (window[i+1] > window[j+1]) begin tmp1 = window[i+1]; window[i+1] = window[j+1]; window[j+1] = tmp1; end
      for (i = 0; i < 4; i = i + 1)
        for (j = i + 1; j < 5; j = j + 1)
          if (window[i+2] > window[j+2]) begin tmp2 = window[i+2]; window[i+2] = window[j+2]; window[j+2] = tmp2; end
      for (i = 0; i < 3; i = i + 1)
        for (j = i + 1; j < 4; j = j + 1)
          if (window[i+3] > window[j+3]) begin tmp3 = window[i+3]; window[i+3] = window[j+3]; window[j+3] = tmp3; end
      for (i = 0; i < 2; i = i + 1)
        for (j = i + 1; j < 3; j = j + 1)
          if (window[i+4] > window[j+4]) begin tmp4 = window[i+4]; window[i+4] = window[j+4]; window[j+4] = tmp4; end
      for (i = 0; i < 1; i = i + 1)
        for (j = i + 1; j < 2; j = j + 1)
          if (window[i+5] > window[j+5]) begin tmp5 = window[i+5]; window[i+5] = window[j+5]; window[j+5] = tmp5; end
      y <= {8'b0, window[3]};
    end
  end
endmodule