module mod8_counter__base__3 (
    input  wire clk,
    input  wire rst_n,
    output reg  [2:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 3'b000;
    end else begin
        if (count == 3'b111) begin
            count <= 3'b000;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule