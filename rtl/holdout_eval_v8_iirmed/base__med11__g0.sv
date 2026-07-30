module base__med11__g0 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);

  reg [7:0] window [0:10]; // array to represent the 11-sample window
  integer i, j, k, temp;

  always @(posedge clk) begin
    if (!rst_n) begin // clear all state on rst_n
      y <= 0;
      for (i = 0; i < 11; i = i + 1) begin
        window[i] <= 0;
      end
    end
    else begin
      window[0] <= x; // insert the current sample at index 0
      for (j = 0; j < 10; j = j + 1) begin
        window[j+1] <= window[j]; // shift the window to make room for the new sample
      end
      for (k = 0; k < 11; k = k + 1) begin // perform bubble sort on the window
        for (i = 10; i >= k; i = i - 1) begin
          if (window[i] < window[i - 1]) begin
            temp = window[i];
            window[i] = window[i - 1];
            window[i - 1] = temp;
          end
        end
      end
      y = {16'b0, window[5]}; // output the median of the window
    end
  end

endmodule