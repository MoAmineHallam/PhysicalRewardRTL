module mod16_counter__base__3 (
    input  wire clk,
    input  wire rst_n,
    output reg  [3:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 4'b0000;
    end else begin
        if (count == 4'b1111) begin
            count <= 4'b0000;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule