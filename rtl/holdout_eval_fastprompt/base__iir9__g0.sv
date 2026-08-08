module base__iir9__g0 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);

  reg [7:0] x_delay[0:9];
  reg [15:0] y_delay[0:1];
  
  integer i;
  reg [15:0] temp;
  
  always @(posedge clk) begin
    if (!rst_n) begin
      y <= 16'b0;
      for (i = 0; i < 10; i = i + 1) begin
        x_delay[i] <= 8'b0;
      end
      y_delay[0] <= 16'b0;
      y_delay[1] <= 16'b0;
    end
    else begin
      y <= temp;
      x_delay[0] <= x;
      for (i = 1; i < 10; i = i + 1) begin
        x_delay[i] <= x_delay[i-1];
      end
      y_delay[0] <= temp;
      y_delay[1] <= y_delay[0];
    end
  end
  
  always @(*) begin
    temp = (3*x_delay[0]) + (5*x_delay[1]) + (7*x_delay[2]) + (9*x_delay[3]) + (11*x_delay[4]) + (13*x_delay[5]) + (15*x_delay[6]) + (17*x_delay[7]) + (19*x_delay[8]) + (21*x_delay[9]) + ((9*y_delay[0])>>4) + ((5*y_delay[1])>>4);
    temp = temp & 16'hFFFF;
  end
  
endmodule