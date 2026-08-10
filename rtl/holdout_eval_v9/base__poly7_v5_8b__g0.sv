module base__poly7_v5_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 16'b0;
    end else begin
        y <= ((((((((53 * x + 68) * x + 36) * x + 67) * x + 8) * x + 1) * x + 93) * x + 82) % 2**16);
    end
end

endmodule