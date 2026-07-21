module apiplain__med7__g1 (
  input clk, 
  input rst_n, 
  input [7:0] x, 
  output reg [15:0] y
);

  // Shift register to hold the 7-sample window
  reg [7:0] window [0:6];
  
  // Temporary wires for median computation
  wire [7:0] w0, w1, w2, w3, w4, w5, w6;
  
  integer i, j, k;
  reg [7:0] temp;
  
  // Assign window values to wires for readability
  assign w0 = window[0];
  assign w1 = window[1];
  assign w2 = window[2];
  assign w3 = window[3];
  assign w4 = window[4];
  assign w5 = window[5];
  assign w6 = window[6];
  
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      // Clear all state
      for (i = 0; i < 7; i = i + 1) begin
        window[i] <= 8'd0;
      end
      y <= 16'd0;
    end else begin
      // Shift in new sample (window[0] is oldest, window[6] is newest)
      window[0] <= window[1];
      window[1] <= window[2];
      window[2] <= window[3];
      window[3] <= window[4];
      window[4] <= window[5];
      window[5] <= window[6];
      window[6] <= x;
      
      // Compute median using bubble sort approach (only comparisons)
      // Sort the 7 values and pick the 4th (index 3 after sorting)
      for (i = 0; i < 6; i = i + 1) begin
        for (j = 0; j < 6 - i; j = j + 1) begin
          k = j + 1;
          if (window[j] > window[k]) begin
            temp = window[j];
            window[j] = window[k];
            window[k] = temp;
          end
        end
      end
      
      // After sorting, the median is at position 3 (0-indexed: window[3])
      y <= {8'd0, window[3]};
    end
  end

endmodule