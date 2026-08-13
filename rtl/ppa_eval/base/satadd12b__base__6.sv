module satadd12b__base__6 (
    input  wire clk, rst_n,
    input  wire [11:0] a,
    input  wire [11:0] b,
    output reg  [11:0] sum
);

always @(posedge clk) begin
    if (~rst_n) begin
        sum <= 0;
    end else begin
        sum <= (a + b) > 12'hFFF ? 12'hFFF : (a + b);
    end
end

endmodule