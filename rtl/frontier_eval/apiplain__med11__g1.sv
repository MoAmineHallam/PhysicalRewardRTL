module apiplain__med11__g1 (
  input clk, 
  input rst_n, 
  input [7:0] x, 
  output reg [15:0] y
);

  // 11-stage shift register to store window samples
  reg [7:0] window [0:10];
  
  // Intermediate signals for sorting
  reg [7:0] s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10;
  wire [7:0] m01, m23, m45, m67, m89, m1011;
  wire [7:0] m02, m13, m46, m57, m810, m911;
  // ... additional comparison wires
  
  integer i;
  
  // Shift register and reset
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      for (i = 0; i < 11; i = i + 1)
        window[i] <= 8'd0;
      y <= 16'd0;
    end else begin
      // Shift window (FIFO behavior)
      for (i = 0; i < 10; i = i + 1)
        window[i] <= window[i+1];
      window[10] <= x;
      
      // Compute median
      y <= {8'b0, median_calc()};
    end
  end
  
  // Function to compute median using comparison network
  function automatic [7:0] median_calc;
    reg [7:0] arr [0:10];
    reg [7:0] tmp;
    integer i, j;
    begin
      // Copy window to temporary array
      for (i = 0; i < 11; i = i + 1)
        arr[i] = window[i];
      
      // Odd-even transposition sort (enough iterations for median)
      for (i = 0; i < 11; i = i + 1) begin
        for (j = (i % 2); j < 10; j = j + 2) begin
          if (arr[j] > arr[j+1]) begin
            tmp = arr[j];
            arr[j] = arr[j+1];
            arr[j+1] = tmp;
          end
        end
      end
      
      // Return median (6th element, 0-indexed)
      median_calc = arr[5];
    end
  endfunction

endmodule