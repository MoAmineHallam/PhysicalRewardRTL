module sft__med19__g7 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] win0;
  reg [7:0] win1;
  reg [7:0] win2;
  reg [7:0] win3;
  reg [7:0] win4;
  reg [7:0] win5;
  reg [7:0] win6;
  reg [7:0] win7;
  reg [7:0] win8;
  reg [7:0] win9;
  reg [7:0] win10;
  reg [7:0] win11;
  reg [7:0] win12;
  reg [7:0] win13;
  reg [7:0] win14;
  reg [7:0] win15;
  reg [7:0] win16;
  reg [7:0] win17;
  reg [7:0] win18;
  reg [7:0] sorted [0:18];
  reg [7:0] temp;
  integer i, j, k;
  always @(posedge clk) begin
    if (!rst_n) begin
      y<=0; win0<=0; win1<=0; win2<=0; win3<=0; win4<=0; win5<=0; win6<=0; win7<=0; win8<=0; win9<=0; win10<=0; win11<=0; win12<=0; win13<=0; win14<=0; win15<=0; win16<=0; win17<=0; win18<=0;
    end else begin
      sorted[0] = x;
      sorted[1] = win0;
      sorted[2] = win1;
      sorted[3] = win2;
      sorted[4] = win3;
      sorted[5] = win4;
      sorted[6] = win5;
      sorted[7] = win6;
      sorted[8] = win7;
      sorted[9] = win8;
      sorted[10] = win9;
      sorted[11] = win10;
      sorted[12] = win11;
      sorted[13] = win12;
      sorted[14] = win13;
      sorted[15] = win14;
      sorted[16] = win15;
      sorted[17] = win16;
      sorted[18] = win17;
      for (i = 0; i < 19; i = i + 1)
        for (j = 0; j < 19 - i - 1; j = j + 1)
          if (sorted[j] > sorted[j+1]) begin
            temp = sorted[j];
            sorted[j] = sorted[j+1];
            sorted[j+1] = temp;
          end
      y <= {8'b0, sorted[9]};
      win18<=win17; win17<=win16; win16<=win15; win15<=win14; win14<=win13; win13<=win12; win12<=win11; win11<=win10; win10<=win9; win9<=win8; win8<=win7; win7<=win6; win6<=win5; win5<=win4; win4<=win3; win3<=win2; win2<=win1; win1<=win0; win0 <= x;
    end
  end
endmodule
