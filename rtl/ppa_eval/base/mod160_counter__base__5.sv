module mod160_counter__base__5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        count <= 8'h00;
    end else begin
        if (count == 8'h9F) begin
            count <= 8'h00;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule