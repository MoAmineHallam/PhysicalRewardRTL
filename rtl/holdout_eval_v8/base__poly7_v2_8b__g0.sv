module base__poly7_v2_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 0;
        end
        else begin
            y <= ((((((((72 * x + 67) * x + 4) * x + 10) * x + 88) * x + 75) * x + 86) * x + 39) & 16'hFFFF);
        end
    end

endmodule