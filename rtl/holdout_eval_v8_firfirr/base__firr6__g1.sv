module base__firr6__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap1, tap2, tap3, tap4, tap5, tap6;
    reg [15:0] acc;

    always @(posedge clk) begin
        if (!rst_n) begin
            tap1 <= 0;
            tap2 <= 0;
            tap3 <= 0;
            tap4 <= 0;
            tap5 <= 0;
            tap6 <= 0;
            acc <= 0;
            y <= 0;
        end
        else begin
            tap1 <= x;
            tap2 <= tap1;
            tap3 <= tap2;
            tap4 <= tap3;
            tap5 <= tap4;
            tap6 <= tap5;
            acc <= (tap1 * 1) + (tap2 * 2) + (tap3 * 3) + (tap4 * 4) + (tap5 * 5) + (tap6 * 6);
            y <= acc;
        end
    end

endmodule