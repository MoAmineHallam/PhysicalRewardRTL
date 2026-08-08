module base__iir16__g0 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);

  parameter B0 = 3;
  parameter B1 = 5;
  parameter B2 = 7;
  parameter B3 = 9;
  parameter B4 = 11;
  parameter B5 = 13;
  parameter B6 = 15;
  parameter B7 = 17;
  parameter B8 = 19;
  parameter B9 = 21;
  parameter B10 = 23;
  parameter B11 = 25;
  parameter B12 = 27;
  parameter B13 = 29;
  parameter B14 = 31;
  parameter B15 = 33;
  parameter B16 = 35;

  reg [15:0] x_1;
  reg [15:0] x_2;
  reg [15:0] x_3;
  reg [15:0] x_4;
  reg [15:0] x_5;
  reg [15:0] x_6;
  reg [15:0] x_7;
  reg [15:0] x_8;
  reg [15:0] x_9;
  reg [15:0] x_10;
  reg [15:0] x_11;
  reg [15:0] x_12;
  reg [15:0] x_13;
  reg [15:0] x_14;
  reg [15:0] x_15;
  reg [15:0] x_16;

  reg [15:0] y_1;
  reg [15:0] y_2;

  always @(posedge clk) begin
    if (!rst_n) begin
      x_1 <= 16'b0;
      x_2 <= 16'b0;
      x_3 <= 16'b0;
      x_4 <= 16'b0;
      x_5 <= 16'b0;
      x_6 <= 16'b0;
      x_7 <= 16'b0;
      x_8 <= 16'b0;
      x_9 <= 16'b0;
      x_10 <= 16'b0;
      x_11 <= 16'b0;
      x_12 <= 16'b0;
      x_13 <= 16'b0;
      x_14 <= 16'b0;
      x_15 <= 16'b0;
      x_16 <= 16'b0;
      y_1 <= 16'b0;
      y_2 <= 16'b0;
      y <= 16'b0;
    end
    else begin
      x_1 <= x;
      x_2 <= x_1;
      x_3 <= x_2;
      x_4 <= x_3;
      x_5 <= x_4;
      x_6 <= x_5;
      x_7 <= x_6;
      x_8 <= x_7;
      x_9 <= x_8;
      x_10 <= x_9;
      x_11 <= x_10;
      x_12 <= x_11;
      x_13 <= x_12;
      x_14 <= x_13;
      x_15 <= x_14;
      x_16 <= x_15;
      y_1 <= ((B0*x)
            + (B1*x_1)
            + (B2*x_2)
            + (B3*x_3)
            + (B4*x_4)
            + (B5*x_5)
            + (B6*x_6)
            + (B7*x_7)
            + (B8*x_8)
            + (B9*x_9)
            + (B10*x_10)
            + (B11*x_11)
            + (B12*x_12)
            + (B13*x_13)
            + (B14*x_14)
            + (B15*x_15)
            + (B16*x_16)
              + ((9*y_1)>>4)
              + ((5*y_2)>>4)) & 16'hFFFF;
      y_2 <= y_1;
      y <= y_1;
    end
  end
endmodule