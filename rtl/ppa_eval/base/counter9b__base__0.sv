module counter9b__base__0 (
    input  wire clk,
    input  wire rst_n,
    output reg  [8:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 9'b0;
    end else begin
        count <= count + 1;
    end
end

endmodule