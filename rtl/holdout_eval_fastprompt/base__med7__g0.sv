module base__med7__g0 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);

  parameter WIDTH = 8;
  parameter DEPTH = 7;

  reg [WIDTH-1:0] window [DEPTH-1:0];
  integer i, j, min_idx, temp;
  reg [15:0] temp_y;

  always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
      for (i = 0; i < DEPTH; i = i + 1) begin
        window[i] <= 0;
      end
      y <= 0;
    end
    else begin
      // shift the window
      for (i = 0; i < DEPTH - 1; i = i + 1) begin
        window[i+1] <= window[i];
      end
      // add the new sample to the end of the window
      window[0] <= x;

      // sort the window using bubble sort
      for (i = 0; i < DEPTH - 1; i = i + 1) begin
        for (j = 0; j < DEPTH - i - 1; j = j + 1) begin
          if (window[j] > window[j+1]) begin
            temp = window[j];
            window[j] = window[j+1];
            window[j+1] = temp;
          end
        end
      end

      // find the median
      if (DEPTH % 2 == 0) begin
        temp_y[15:0] <= {window[DEPTH/2 - 1], window[DEPTH/2]};
      end
      else begin
        temp_y[15:0] <= {16'b0, window[DEPTH/2]};
      end

      // output the median
      y <= temp_y;
    end
  end

endmodule