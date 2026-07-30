module grpo__med11__g8 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] w0;
  reg [7:0] w1;
  reg [7:0] w2;
  reg [7:0] w3;
  reg [7:0] w4;
  reg [7:0] w5;
  reg [7:0] w6;
  reg [7:0] w7;
  reg [7:0] w8;
  reg [7:0] w9;
  reg [7:0] w10;
  reg [7:0] s [0:10];
  reg [7:0] t;
  integer i, j;
  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 16'd0;
      w0 <= 8'd0; w1 <= 8'd0; w2 <= 8'd0; w3 <= 8'd0; w4 <= 8'd0;
      w5 <= 8'd0; w6 <= 8'd0; w7 <= 8'd0; w8 <= 8'd0; w9 <= 8'd0;
      w10 <= 8'd0;
    end else begin
      s[0] = x;
      s[1] = w0;
      s[2] = w1;
      s[3] = w2;
      s[4] = w3;
      s[5] = w4;
      s[6] = w5;
      s[7] = w6;
      s[8] = w7;
      s[9] = w8;
      s[10] = w9;
      for (i = 0; i < 11; i = i + 1)
        for (j = 0; j < 11 - i - 1; j = j + 1)
          if (s[j] > s[j+1]) begin
            t = s[j];
            s[j] = s[j+1];
            s[j+1] = t;
          end
      y <= {8'b0, s[5]};
      w10 <= w9;
      w9 <= w8;
      w8 <= w7;
      w7 <= w6;
      w6 <= w5;
      w5 <= w4;
      w4 <= w3;
      w3 <= w2;
      w2 <= w1;
      w1 <= w0;
      w0 <= x;
    end
  end
endmodule