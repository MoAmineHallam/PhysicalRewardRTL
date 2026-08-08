module base__med7__g1 (
  input clk, input rst_n, input [7:0] x, output reg [15:0] y
);

  reg [7:0] buffer [6:0];
  reg [2:0] buffer_ptr;
  reg [7:0] sorted_buffer [6:0];

  integer i;
  integer j;
  integer k;

  always @(posedge clk) begin
    if (!rst_n) begin
      buffer_ptr <= 0;
      for (i = 0; i < 7; i = i + 1) begin
        sorted_buffer[i] <= 0;
        buffer[i] <= 0;
      end
    end else begin
      // Insert new sample into buffer
      buffer[buffer_ptr] <= x;

      // Sort buffer
      for (i = 0; i < 7; i = i + 1) begin
        sorted_buffer[i] <= buffer[(buffer_ptr - i + 7) % 7];
      end
      for (i = 0; i < 7; i = i + 1) begin
        for (j = 0; j < 7 - i - 1; j = j + 1) begin
          if (sorted_buffer[j] > sorted_buffer[j + 1]) begin
            k = sorted_buffer[j];
            sorted_buffer[j] = sorted_buffer[j + 1];
            sorted_buffer[j + 1] = k;
          end
        end
      end

      // Output median
      y <= {16'b0, sorted_buffer[3]};

      // Advance buffer pointer
      buffer_ptr <= (buffer_ptr + 1) % 7;
    end
  end
endmodule