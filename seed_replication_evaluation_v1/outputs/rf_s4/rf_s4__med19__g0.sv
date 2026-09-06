module rf_s4__med19__g0 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] window [0:18];
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
  integer i, j, k;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 19; i = i + 1) window[i] <= 8'd0;
      y <= 16'd0;
    end else begin
      window[0] <= x;
      for (i = 1; i < 19; i = i + 1) window[i] <= window[i-1];
      for (i = 0; i < 18; i = i + 1) begin
        for (j = i + 1; j < 19; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp0 = window[i];
            window[i] = window[j];
            window[j] = tmp0;
          end
        end
      end
      for (i = 0; i < 17; i = i + 1) begin
        for (j = i + 1; j < 18; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp1 = window[i];
            window[i] = window[j];
            window[j] = tmp1;
          end
        end
      end
      for (i = 0; i < 16; i = i + 1) begin
        for (j = i + 1; j < 17; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp2 = window[i];
            window[i] = window[j];
            window[j] = tmp2;
          end
        end
      end
      for (i = 0; i < 15; i = i + 1) begin
        for (j = i + 1; j < 16; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp3 = window[i];
            window[i] = window[j];
            window[j] = tmp3;
          end
        end
      end
      for (i = 0; i < 14; i = i + 1) begin
        for (j = i + 1; j < 15; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp4 = window[i];
            window[i] = window[j];
            window[j] = tmp4;
          end
        end
      end
      for (i = 0; i < 13; i = i + 1) begin
        for (j = i + 1; j < 14; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp5 = window[i];
            window[i] = window[j];
            window[j] = tmp5;
          end
        end
      end
      for (i = 0; i < 12; i = i + 1) begin
        for (j = i + 1; j < 13; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp6 = window[i];
            window[i] = window[j];
            window[j] = tmp6;
          end
        end
      end
      for (i = 0; i < 11; i = i + 1) begin
        for (j = i + 1; j < 12; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp7 = window[i];
            window[i] = window[j];
            window[j] = tmp7;
          end
        end
      end
      for (i = 0; i < 10; i = i + 1) begin
        for (j = i + 1; j < 11; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp8 = window[i];
            window[i] = window[j];
            window[j] = tmp8;
          end
        end
      end
      for (i = 0; i < 9; i = i + 1) begin
        for (j = i + 1; j < 10; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp9 = window[i];
            window[i] = window[j];
            window[j] = tmp9;
          end
        end
      end
      for (i = 0; i < 8; i = i + 1) begin
        for (j = i + 1; j < 9; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp10 = window[i];
            window[i] = window[j];
            window[j] = tmp10;
          end
        end
      end
      for (i = 0; i < 7; i = i + 1) begin
        for (j = i + 1; j < 8; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp11 = window[i];
            window[i] = window[j];
            window[j] = tmp11;
          end
        end
      end
      for (i = 0; i < 6; i = i + 1) begin
        for (j = i + 1; j < 7; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp12 = window[i];
            window[i] = window[j];
            window[j] = tmp12;
          end
        end
      end
      for (i = 0; i < 5; i = i + 1) begin
        for (j = i + 1; j < 6; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp13 = window[i];
            window[i] = window[j];
            window[j] = tmp13;
          end
        end
      end
      for (i = 0; i < 4; i = i + 1) begin
        for (j = i + 1; j < 5; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp14 = window[i];
            window[i] = window[j];
            window[j] = tmp14;
          end
        end
      end
      for (i = 0; i < 3; i = i + 1) begin
        for (j = i + 1; j < 4; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp15 = window[i];
            window[i] = window[j];
            window[j] = tmp15;
          end
        end
      end
      for (i = 0; i < 2; i = i + 1) begin
        for (j = i + 1; j < 3; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp16 = window[i];
            window[i] = window[j];
            window[j] = tmp16;
          end
        end
      end
      for (i = 0; i < 1; i = i + 1) begin
        for (j = i + 1; j < 2; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp17 = window[i];
            window[i] = window[j];
            window[j] = tmp17;
          end
        end
      end
      y <= {8'b0, window[9]};
    end
  end
endmodule
