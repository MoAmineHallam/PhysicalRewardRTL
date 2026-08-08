module base__firr6__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] tap [0:5];
reg [15:0] sum;

always @(posedge clk) begin
    if (!rst_n) begin
        for (int i = 0; i < 6; i = i + 1) begin
            tap[i] <= 8'b0;
        end
        sum <= 16'b0;
        y <= 16'b0;
    end else begin
        tap[0] <= x;
        for (int i = 1; i < 6; i = i + 1) begin
            tap[i] <= tap[i-1];
        end
        sum <= tap[0]*(1) + tap[1]*(2) + tap[2]*(3) + tap[3]*(4) + tap[4]*(5) + tap[5]*(6);
        y <= sum;
    end
end

endmodule