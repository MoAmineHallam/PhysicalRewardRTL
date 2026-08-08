module base__med7__g0 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);

  reg [15:0] sample [6:0];
  integer i, j, k;
  reg [15:0] temp;

  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 0;
      for (i = 0; i < 7; i = i + 1) begin
        sample[i] <= 0;
      end
    end
    else begin
      sample[6] <= x == 0 ? 16'h00 : {1'b0, x};
      for (i = 0; i < 6; i = i + 1) begin
        sample[i] <= sample[i + 1];
      end
      
      for (i = 0; i < 7; i = i + 1) begin
        for (j = 0; j < 6; j = j + 1) begin
          if (sample[j] > sample[j + 1]) begin
            temp = sample[j];
            sample[j] = sample[j + 1];
            sample[j + 1] = temp;
          end
        end
      end

      y <= sample[3];
    end
  end
endmodule