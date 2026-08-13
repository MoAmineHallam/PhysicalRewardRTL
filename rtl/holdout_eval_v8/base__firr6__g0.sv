module base__firr6__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] tap0, tap1, tap2, tap3, tap4, tap5;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        tap0 <= 0;
        tap1 <= 0;
        tap2 <= 0;
        tap3 <= 0;
        tap4 <= 0;
        tap5 <= 0;
        y <= 0;
    end
    else begin
        tap0 <= x;
        tap1 <= tap0;
        tap2 <= tap1;
        tap3 <= tap2;
        tap4 <= tap3;
        tap5 <= tap4;
        y <= tap0 * 1 + tap1 * 2 + tap2 * 3 + tap3 * 4 + tap4 * 5 + tap5 * 6;
    end
end

endmodule