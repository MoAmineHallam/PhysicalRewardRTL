module base__firr6__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap0;
    reg [7:0] tap1;
    reg [7:0] tap2;
    reg [7:0] tap3;
    reg [7:0] tap4;
    reg [7:0] tap5;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tap0 <= 8'b0;
            tap1 <= 8'b0;
            tap2 <= 8'b0;
            tap3 <= 8'b0;
            tap4 <= 8'b0;
            tap5 <= 8'b0;
            y <= 16'b0;
        end else begin
            tap0 <= x;
            tap1 <= tap0;
            tap2 <= tap1;
            tap3 <= tap2;
            tap4 <= tap3;
            tap5 <= tap4;
            y <= (tap0 * 1) + (tap1 * 2) + (tap2 * 3) + (tap3 * 4) + (tap4 * 5) + (tap5 * 6);
        end
    end

endmodule