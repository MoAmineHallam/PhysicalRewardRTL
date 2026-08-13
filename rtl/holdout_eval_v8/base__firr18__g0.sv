module base__firr18__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] tap [0:17];
integer k;

always @(posedge clk) begin
    if (!rst_n) begin
        y <= 0;
        for (k = 0; k < 18; k = k + 1) begin
            tap[k] <= 0;
        end
    end else begin
        tap[0] <= x;
        y <= (tap[0]*(1) + tap[1]*(2) + tap[2]*(3) + tap[3]*(4) + tap[4]*(5) + tap[5]*(6) + tap[6]*(7) + tap[7]*(8) + tap[8]*(9) + tap[9]*(10) + tap[10]*(11) + tap[11]*(12) + tap[12]*(13) + tap[13]*(14) + tap[14]*(15) + tap[15]*(16) + tap[16]*(17) + tap[17]*(18)) & 16'hffff;
        for (k = 17; k > 0; k = k - 1) begin
            tap[k] <= tap[k-1];
        end
    end
end

endmodule