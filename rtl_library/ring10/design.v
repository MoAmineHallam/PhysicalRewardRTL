// 10-bit ring counter (one-hot, rotates).
module ring10 (
    input  wire clk, rst_n,
    output reg  [9:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 10'b1;
        else        count <= {count[8:0], count[9]};
    end
endmodule
