module mlp_s1__med19__g8 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] window [0:18];
  reg [7:0] sorted [0:18];
  integer i, j, k;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 19; i = i + 1) begin
        window[i] <= 8'd0;
        sorted[i] <= 8'd0;
      end
      y <= 16'd0;
    end else begin
      window[0] <= x;
      for (i = 1; i < 19; i = i + 1) begin
        window[i] <= window[i-1];
      end
      for (i = 0; i < 19; i = i + 1) begin
        sorted[i] <= window[i];
      end
      for (i = 0; i < 19; i = i + 1) begin
        for (j = i + 1; j < 19; j = j + 1) begin
          if (sorted[i] > sorted[j]) begin
            k = sorted[i];
            sorted[i] = sorted[j];
            sorted[j] = k;
          end
        end
      end
      y <= {8'd0, sorted[9]};
    end
  end
endmodule
