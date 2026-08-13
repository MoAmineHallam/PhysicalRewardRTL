module satadd12b__base__3 (
    input  wire clk, rst_n,
    input  wire [11:0] a,
    input  wire [11:0] b,
    output reg  [11:0] sum
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        sum <= 0;
    end else begin
        if ((a + b) > 4095) begin
            sum <= 4095;
        end else begin
            sum <= a + b;
        end
    end
end

endmodule