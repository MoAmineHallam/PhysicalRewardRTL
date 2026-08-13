module counter8b__base__0 (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 8'b0;
    end else begin
        if (count == 8'b1111_1111) begin
            count <= 8'b0;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule