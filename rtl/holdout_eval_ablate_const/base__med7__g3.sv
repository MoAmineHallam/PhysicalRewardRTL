module base__med7__g3 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);

  reg [7:0] window[6:0];
  integer i, j, temp;

  always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
      y <= 16'd0;
      for (i = 0; i < 7; i = i + 1) begin
        window[i] <= 8'd0;
      end
    end else begin
      // insert new sample to the window
      window[0] <= x;
      // shift window to the right
      for (i = 1; i < 7; i = i + 1) begin
        window[i] <= window[i-1];
      end
      // sort window using bubble sort
      for (i = 0; i < 7-1; i = i + 1) begin
        for (j = 0; j < 7-1-i; j = j + 1) begin
          if (window[j] > window[j+1]) begin
            temp = window[j+1];
            window[j+1] = window[j];
            window[j] = temp;
          end
        end
      end
      // assign the median to y
      y <= {16'd0, window[3]};
    end
  end
endmodule