module rf_s4__med21__g3 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] window [0:20];
  reg [7:0] tmp;
  integer i, j, k;
  reg [7:0] tmp2;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 21; i = i + 1) window[i] <= 8'd0;
      y <= 16'd0;
    end else begin
      window[0] <= x;
      for (i = 1; i < 21; i = i + 1) begin
        window[i] <= window[i-1];
      end
      for (i = 0; i < 20; i = i + 1) begin
        for (j = i + 1; j < 21; j = j + 1) begin
          if (window[i] > window[j]) begin
            tmp = window[i];
            window[i] = window[j];
            window[j] = tmp;
          end
        end
      end
      y <= {8'b0, window[10]};
    end
  end
endmodule
