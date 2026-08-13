module counter16b__base__7 (
    input  wire clk,
    input  wire rst_n,
    output reg  [15:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 16'b0;
    end else begin
        count <= count + 16'b1;
    end
end

endmodule