module base__poly4_v6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [15:0] result;

    always @(posedge clk) begin
        if (!rst_n) begin
            result <= 0;
        end else begin
            result <= x*x*x*x*65 + x*x*x*29 + x*x*88 + x*44 + 17;
        end
    end

    assign y = result[15:0];

endmodule