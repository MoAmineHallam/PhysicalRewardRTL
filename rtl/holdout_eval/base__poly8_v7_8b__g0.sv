module base__poly8_v7_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
        end else begin
            y <= ((((((((57*x)+11)*x+20)*x+96)*x+53)*x+74)*x+25)*x+52)*x+15;
        end
    end

endmodule