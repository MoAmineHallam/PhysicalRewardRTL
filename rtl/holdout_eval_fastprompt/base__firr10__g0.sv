module base__firr10__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] tap [0:9];

always @(posedge clk) begin
    if (!rst_n) begin
        for (int i = 0; i < 10; i = i + 1) begin
            tap[i] <= 8'b0;
        end
        y <= 16'b0;
    end else begin
        tap[0] <= x;
        for (int i = 0; i < 9; i = i + 1) begin
            tap[i+1] <= tap[i];
        end
        y <= (1*tap[0]) + (2*tap[1]) + (3*tap[2]) + (4*tap[3]) + (5*tap[4]) + (6*tap[5]) + (7*tap[6]) + (8*tap[7]) + (9*tap[8]) + (10*tap[9]);
    end
end

endmodule