// 9-bit ring counter (one-hot, rotates).
module ring9 (
    input  wire clk, rst_n,
    output reg  [8:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 9'b1;
        else        count <= {count[7:0], count[8]};
    end
endmodule
