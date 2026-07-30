module base__poly4_v6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [15:0] y_tmp;

always @(posedge clk) begin
    if (!rst_n) begin
        y <= 0;
        y_tmp <= 0;
    end else begin
        y_tmp <= (x * (x * (x * (x * 65 +29) +88) +44) +17) % (2**16);
        y <= y_tmp;
    end
end

endmodule