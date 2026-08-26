module mlp_s1__poly12_v15_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
        end else begin
            y <= ((((((((((((((48 * x + 24) * x + 79) * x + 2) * x + 46) * x + 35) * x + 44) * x + 66) * x + 80) * x + 64) * x + 18) * x + 58) * x + 51)) & 16'hFFFF);
        end
    end
endmodule
