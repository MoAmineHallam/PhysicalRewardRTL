module grpo__med11__g11 (
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
  reg [7:0] arr [0:10];
  reg [7:0] sorted [0:10];
  reg [3:0] i;
  reg [3:0] j;
  reg [7:0] tmp;
  reg [7:0] med;
  reg [15:0] y_reg;
  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 0; w0 <= 0; w1 <= 0; w2 <= 0; w3 <= 0; w4 <= 0; w5 <= 0; w6 <= 0; w7 <= 0; w8 <= 0; w9 <= 0;
    end else begin
      arr[0] = x;
      arr[1] = w0;
      arr[2] = w1;
      arr[3] = w2;
      arr[4] = w3;
      arr[5] = w4;
      arr[6] = w5;
      arr[7] = w6;
      arr[8] = w7;
      arr[9] = w8;
      arr[10] = w9;
      for (i = 0; i < 11; i = i + 1) begin
        for (j = i + 1; j < 11; j = j + 1) begin
          if (arr[i] > arr[j]) begin
            tmp = arr[i];
            arr[i] = arr[j];
            arr[j] = tmp;
          end
        end
        sorted[i] = arr[i];
      end
      med = sorted[5];
      y_reg <= {8'b0, med};
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
      y <= y_reg;
    end
  end
endmodule