module sft__med21__g10 (
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
  reg [7:0] w11;
  reg [7:0] w12;
  reg [7:0] w13;
  reg [7:0] w14;
  reg [7:0] w15;
  reg [7:0] w16;
  reg [7:0] w17;
  reg [7:0] w18;
  reg [7:0] w19;
  reg [7:0] w0a;
  reg [7:0] w1a;
  reg [7:0] w2a;
  reg [7:0] w3a;
  reg [7:0] w4a;
  reg [7:0] w5a;
  reg [7:0] w6a;
  reg [7:0] w7a;
  reg [7:0] w8a;
  reg [7:0] w9a;
  reg [7:0] w10a;
  reg [7:0] w11a;
  reg [7:0] w12a;
  reg [7:0] w13a;
  reg [7:0] w14a;
  reg [7:0] w15a;
  reg [7:0] w16a;
  reg [7:0] w17a;
  reg [7:0] w18a;
  reg [7:0] w19a;
  reg [7:0] a[0:20];
  integer i, j, t;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 21; i = i + 1) a[i] <= 8'd0;
      y<=16'd0;
    end else begin
      a[0]<=x;
      for (i = 1; i < 21; i = i + 1) a[i]<=a[i-1];
      for (i = 0; i < 20; i = i + 1)
        for (j = i+1; j < 21; j = j + 1)
          if (a[i]>a[j]) begin t=a[i]; a[i]=a[j]; a[j]=t; end
      y <= {8'b0, a[10]};
    end
  end
endmodule
