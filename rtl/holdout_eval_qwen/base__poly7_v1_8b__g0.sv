module base__poly7_v1_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg  [15:0] tmp;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 0;
    end else begin
        tmp = 16;  // c0 coefficient
        tmp = tmp * x + 91;  // c1 coefficient
        tmp = tmp * x + 42;  // c2 coefficient
        tmp = tmp * x + 85;  // c3 coefficient
        tmp = tmp * x + 48;  // c4 coefficient
        tmp = tmp * x + 89;  // c5 coefficient
        tmp = tmp * x + 88;  // c6 coefficient
        tmp = tmp * x + 18;  // c7 coefficient

        // Ensure only the lower 16 bits are kept
        y <= tmp & 16'hFFFF;
    end
end

endmodule