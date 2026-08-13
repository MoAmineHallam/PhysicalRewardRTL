module updown14b__base__4 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [13:0] count
);

  always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
      count <= 0;
    end else if (dir) begin
      count <= count - 1;
    end else begin
      count <= count + 1;
    end
  end

endmodule