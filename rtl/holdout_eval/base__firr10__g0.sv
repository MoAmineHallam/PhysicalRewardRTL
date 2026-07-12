module base__firr10__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap[0:9];
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (~rst_n) begin
            for (i=0; i<10; i=i+1) begin
                tap[i] <= 0;
            end
            y <= 0;
        end
        else begin
            // shift in new sample and push new value into first position of delay line
            tap[0] <= x;
            for (i=9; i>0; i=i-1) begin
                tap[i] <= tap[i-1];
            end
            // compute output
            y <= (tap[0]*(1)) + (tap[1]*(2)) + (tap[2]*(3)) + (tap[3]*(4)) + (tap[4]*(5)) + (tap[5]*(6)) + (tap[6]*(7)) + (tap[7]*(8)) + (tap[8]*(9)) + (tap[9]*(10));
        end
    end

endmodule