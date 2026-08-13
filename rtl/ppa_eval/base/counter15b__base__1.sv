module counter15b__base__1 (
    input  wire clk,
    input  wire rst_n,
    output reg  [14:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 15'b0;
    end else begin
        count <= count + 1;
    end
end

endmodule