module mlp_s1__med19__g7 (
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
  reg [7:0] tmpx;
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
      y <= {8'b0, window[9]};
    end
  end
endmodule
