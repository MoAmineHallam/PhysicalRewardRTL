// 7-bit ring counter (one-hot, rotates).
module ring7 (
    input  wire clk, rst_n,
    output reg  [6:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 7'b1;
        else        count <= {count[5:0], count[6]};
    end
endmodule
