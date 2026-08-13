module mod16_counter__v4_s100__2 (
    input  wire clk,
    input  wire rst_n,
    output reg  [3:0] count
);

reg [3:0] count_reg;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count_reg <= 4'b0;
    end else begin
        count_reg <= count_reg + 1;
    end
end

assign count = count_reg;

endmodule