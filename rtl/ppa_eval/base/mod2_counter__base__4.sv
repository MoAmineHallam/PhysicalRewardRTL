module mod2_counter__base__4 (
    input  wire clk,
    input  wire rst_n,
    output reg  [0:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 1'b0;
    end
    else begin
        count <= ~count;
    end
end

endmodule