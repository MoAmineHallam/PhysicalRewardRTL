module base__firr18__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] tap [0:17];

integer i;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 0;
        for (i = 0; i < 18; i = i + 1) begin
            tap[i] <= 0;
        end
    end
    else begin
        y <= sum();
        for (i = 17; i > 0; i = i - 1) begin
            tap[i] <= tap[i-1];
        end
        tap[0] <= x;
    end
end

function [15:0] sum();
    integer j;
    sum = 0;
    for (j = 0; j < 18; j = j + 1) begin
        sum = sum + (j+1)*tap[j];
    end
endfunction

endmodule