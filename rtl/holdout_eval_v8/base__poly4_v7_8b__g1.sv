module base__poly4_v7_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
        end else begin
            y <= (((((24*x + 36)*x + 17)*x + 21)*x + 50) & 16'hFFFF);
        end
    end

endmodule