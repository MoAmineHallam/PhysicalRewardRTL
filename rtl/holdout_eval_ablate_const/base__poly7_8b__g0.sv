module base__poly7_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 0;
        end else begin
            y <= (((((((((x * 1) + 3) * x + 5) * x + 7) * x + 9) * x + 11) * x + 13) * x + 15) % 65536);
        end
    end

endmodule