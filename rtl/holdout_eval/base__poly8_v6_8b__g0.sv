module base__poly8_v6_8b__g0(
    input wire clk,
    input wire rst_n,
    input wire [7:0] x,
    output reg [15:0] y
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        y <= 16'b0;
    end else begin
        y <= (((((((((92 * x) + 96) * x + 7) * x + 62) * x + 54) * x + 61) * x + 77) * x + 51) * x + 45);
    end
end

endmodule