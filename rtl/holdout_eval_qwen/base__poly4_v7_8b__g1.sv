module base__poly4_v7_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg  [15:0] temp_y;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 0;
    end else begin
        // Using Horner's rule for polynomial evaluation: y = c0 + x * (c1 + x * (c2 + x * (c3 + x * c4)))
        temp_y <= (50 + x * (21 + x * (17 + x * (36 + x * 24)))) % 65536;
        y <= temp_y;
    end
end

endmodule