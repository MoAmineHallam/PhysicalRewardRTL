module med3__g4 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] w0;
  reg [7:0] w1;
  reg [7:0] s [0:2];
  reg [7:0] t;
  integer i, j;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; w0<=0; w1<=0;
    end else begin
      s[0]=x; s[1]=w0; s[2]=w1;
      for (i = 0; i < 2; i = i + 1)
        for (j = 0; j < 2 - i; j = j + 1)
          if (s[j] > s[j+1]) begin t = s[j]; s[j] = s[j+1]; s[j+1] = t; end
      y <= {8'b0, s[1]};
      w1<=w0; w0<=x;
    end
  end
endmodule