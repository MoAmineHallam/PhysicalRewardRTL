// 12-bit ring counter (one-hot, rotates).
module ring12 (
    input  wire clk, rst_n,
    output reg  [11:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 12'b1;
        else        count <= {count[10:0], count[11]};
    end
endmodule
