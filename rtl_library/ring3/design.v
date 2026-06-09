// 3-bit ring counter (one-hot, rotates).
module ring3 (
    input  wire clk, rst_n,
    output reg  [2:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 3'b1;
        else        count <= {count[1:0], count[2]};
    end
endmodule
