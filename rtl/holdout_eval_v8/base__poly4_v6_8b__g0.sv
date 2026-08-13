module base__poly4_v6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        y <= 16'h0000;
    end else begin
        y <= (((((((65 * x) + 29) * x + 88) * x + 44) * x + 17) % (1<<16)) % (1<<16));
    end
end

endmodule