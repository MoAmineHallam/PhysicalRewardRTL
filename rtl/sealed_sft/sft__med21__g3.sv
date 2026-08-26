module sft__med21__g3 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] window [0:20];
  integer i, j, mid;
  reg [7:0] t;
  reg [15:0] sorted [0:20];
  wire [7:0] l = window[0];
  wire [7:0] h = sorted[20];
  always @(*) begin
    for (i = 0; i < 21; i = i + 1) begin
      sorted[i] = window[i];
      for (j = i; j > 0 && sorted[j] < sorted[j-1]; j = j - 1) begin
        t = sorted[j]; sorted[j] = sorted[j-1]; sorted[j-1] = t;
      end
    end
    mid = (21 - 1) / 2;
    y = (sorted[mid] < sorted[mid+1]) ? sorted[mid] : sorted[mid+1];
  end
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 21; i = i + 1) window[i] <= 8'd0;
      y <= 16'd0;
    end else begin
      window[0] <= x;
      for (i = 1; i < 21; i = i + 1) window[i] <= window[i-1];
    end
  end
endmodule
