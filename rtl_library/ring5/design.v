// 5-bit ring counter (one-hot, rotates).
module ring5 (
    input  wire clk, rst_n,
    output reg  [4:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 5'b1;
        else        count <= {count[3:0], count[4]};
    end
endmodule
