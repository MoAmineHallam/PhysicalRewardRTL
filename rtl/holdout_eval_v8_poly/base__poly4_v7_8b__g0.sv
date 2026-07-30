module base__poly4_v7_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [15:0] coef [4:0];
    assign coef[0] = 50;
    assign coef[1] = 21;
    assign coef[2] = 17;
    assign coef[3] = 36;
    assign coef[4] = 24;

    reg [7:0] x_reg;
    reg [15:0] y_reg;

    always @(posedge clk) begin
        if (!rst_n) begin
            y_reg <= 0;
        end else begin
            x_reg <= x;
            y_reg <= (((coef[4] * x_reg + coef[3]) * x_reg + coef[2]) * x_reg + coef[1]) * x_reg + coef[0];
        end
    end

    assign y = y_reg;

endmodule