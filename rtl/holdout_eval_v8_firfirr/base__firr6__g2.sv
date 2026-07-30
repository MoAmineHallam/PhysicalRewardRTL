module base__firr6__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap [0:5];
    integer k;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (k = 0; k < 6; k = k + 1) begin
                tap[k] <= 0;
            end
            y <= 0;
        end
        else begin
            tap[5] <= tap[4];
            tap[4] <= tap[3];
            tap[3] <= tap[2];
            tap[2] <= tap[1];
            tap[1] <= tap[0];
            tap[0] <= x;
            y <= (tap[0]*(1)) + (tap[1]*(2)) + (tap[2]*(3)) + (tap[3]*(4)) + (tap[4]*(5)) + (tap[5]*(6));
        end
    end
    
endmodule