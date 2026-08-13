module mod128_counter__v4_s100__4 (
    input  wire clk,
    input  wire rst_n,
    output reg  [6:0] count
);

reg [6:0] count_reg;

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count_reg <= 7'b0;
    end else begin
        count_reg <= count_reg + 1;
    end
end

assign count = count_reg;

endmodule