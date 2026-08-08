module base__iir5__g0 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);

  reg [15:0] s1, s2;
  reg [15:0] x1, x2, x3, x4, x5, x6;
  reg [15:0] y1, y2;
  
  always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
      s1 <= 0;
      s2 <= 0;
      x1 <= 0;
      x2 <= 0;
      x3 <= 0;
      x4 <= 0;
      x5 <= 0;
      x6 <= 0;
      y1 <= 0;
      y2 <= 0;
      y <= 0;
    end else begin
      // Shift samples
      x1 <= x;
      x2 <= x1;
      x3 <= x2;
      x4 <= x3;
      x5 <= x4;
      x6 <= x5;
      
      // Calculate sum
      s1 <= 3*x1 + 5*x2 + 7*x3 + 9*x4 + 11*x5 + 13*x6;
      
      // Update outputs
      y1 <= s1 + ((9*y1)>>4) + ((5*y2)>>4);
      y <= y1[15:0];
      
      // Shift outputs
      y2 <= y1;
    end
  end
  
endmodule