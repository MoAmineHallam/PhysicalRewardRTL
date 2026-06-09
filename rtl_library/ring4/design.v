// 4-bit ring counter (one-hot, rotates).
module ring4 (
    input  wire clk, rst_n,
    output reg  [3:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 4'b1;
        else        count <= {count[2:0], count[3]};
    end
endmodule
