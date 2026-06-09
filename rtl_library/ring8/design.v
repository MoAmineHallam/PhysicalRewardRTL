// 8-bit ring counter (one-hot, rotates).
module ring8 (
    input  wire clk, rst_n,
    output reg  [7:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 8'b1;
        else        count <= {count[6:0], count[7]};
    end
endmodule
