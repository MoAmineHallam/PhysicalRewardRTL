module mlp_s1__med19__g4 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] ring [0:18];
  reg [7:0] s [0:18];
  integer i, j, t;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 19; i = i + 1) begin
        ring[i] <= 8'd0;
      end
      y <= 16'd0;
    end else begin
      ring[0] <= x;
      for (i = 1; i < 19; i = i + 1) begin
        ring[i] <= ring[i-1];
      end
      for (i = 0; i < 19; i = i + 1) begin
        s[i] <= ring[i];
      end
      for (i = 0; i < 18; i = i + 1) begin
        for (j = i+1; j < 19; j = j + 1) begin
          if (s[i] > s[j]) begin
            t = s[i];
            s[i] = s[j];
            s[j] = t;
          end
        end
      end
      y <= {8'b0, s[9]};
    end
  end
endmodule
