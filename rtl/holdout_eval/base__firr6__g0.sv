module base__firr6__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap [0:5];
    
    integer i;
    
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
            for (i = 0; i < 6; i = i + 1) begin
                tap[i] <= 0;
            end
        end
        else begin
            for (i = 5; i > 0; i = i - 1) begin
                tap[i] <= tap[i-1];
            end
            tap[0] <= x;
            
            y <= (1*(tap[0]) + 2*(tap[1]) + 3*(tap[2]) + 4*(tap[3]) + 5*(tap[4]) + 6*(tap[5]));
        end
    end
    
endmodule