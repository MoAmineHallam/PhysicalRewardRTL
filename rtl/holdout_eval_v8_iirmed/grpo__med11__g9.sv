module grpo__med11__g9 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] window [0:10];
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
  reg [7:0] t;
  integer i;
  integer j;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 11; i = i + 1) window[i] <= 8'd0;
      y <= 16'd0;
    end else begin
      window[0] <= x;
      for (i = 1; i < 11; i = i + 1) window[i] <= window[i - 1];
      for (i = 0; i < 10; i = i + 1) begin
        for (j = i + 1; j < 11; j = j + 1) begin
          if (window[i] > window[j]) begin
            t = window[i];
            window[i] = window[j];
            window[j] = t;
          end
        end
      end
      y <= {8'd0, window[5]};
    end
  end
endmodule