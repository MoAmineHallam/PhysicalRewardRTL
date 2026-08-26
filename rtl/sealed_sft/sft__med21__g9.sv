module sft__med21__g9 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] window [0:20];
  integer i, j, k;
  reg [7:0] t;
  reg [7:0] sorted [0:20];
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 21; i = i + 1) begin window[i] <= 8'd0; end
      y <= 16'd0;
    end else begin
      window[0] <= x;
      for (i = 1; i < 21; i = i + 1) begin window[i] <= window[i-1]; end
      for (i = 0; i < 21; i = i + 1) begin sorted[i] <= window[i]; end
      for (i = 0; i < 20; i = i + 1) begin
        for (j = i + 1; j < 21; j = j + 1) begin
          if (sorted[i] > sorted[j]) begin
            t = sorted[i]; sorted[i] = sorted[j]; sorted[j] = t;
          end
        end
      end
      y <= {8'b0, sorted[10]};
    end
  end
endmodule
