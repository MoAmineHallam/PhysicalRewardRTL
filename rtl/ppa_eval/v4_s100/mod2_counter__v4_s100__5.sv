module mod2_counter__v4_s100__5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [0:0] count
);

reg [1:0] count_reg;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count_reg <= 2'b00;
    end else begin
        count_reg <= count_reg + 1;
    end
end

assign count = count_reg[0];

endmodule