module mlp_s1__med21__g7 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);
  reg [7:0] u [0:20];
  reg [7:0] t;
  integer i, j;
  always @(posedge clk) begin
    if (!rst_n) begin
      for (i = 0; i < 21; i = i + 1) u[i] <= 8'd0;
      y <= 16'd0;
    end else begin
      u[0] <= x;
      for (i = 1; i < 21; i = i + 1) u[i] <= u[i-1];
      for (i = 0; i < 20; i = i + 1)
        for (j = i + 1; j < 21; j = j + 1)
          if (u[i] > u[j]) begin
            t = u[i];
            u[i] = u[j];
            u[j] = t;
          end
      y <= {8'd0, u[10]};
    end
  end
endmodule
