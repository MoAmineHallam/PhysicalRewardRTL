module mod32_counter__base__2 (
    input  wire clk,
    input  wire rst_n,
    output reg  [4:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 5'b0;
    end else begin
        count <= count + 5'b1;
    end
end

endmodule