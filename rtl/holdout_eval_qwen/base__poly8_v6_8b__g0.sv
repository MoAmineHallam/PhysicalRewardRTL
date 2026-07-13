module base__poly8_v6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg  [15:0] tmp;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 16'b0;
    end else begin
        tmp = 16'd92;
        tmp = tmp * x + 96;
        tmp = tmp * x + 7;
        tmp = tmp * x + 62;
        tmp = tmp * x + 54;
        tmp = tmp * x + 61;
        tmp = tmp * x + 77;
        tmp = tmp * x + 51;
        tmp = tmp * x + 45;
        
        // Keep only the low 16 bits
        y <= tmp;
    end
end

endmodule