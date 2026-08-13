module counter15b__base__3 (
    input  wire clk,
    input  wire rst_n,
    output reg  [14:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 0;
    end else begin
        if (count == 15'h7FFF) begin
            count <= 15'h0000;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule