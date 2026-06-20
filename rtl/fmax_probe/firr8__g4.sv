module firr8__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  tap [0:7];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 8; i = i + 1) tap[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            tap[0] <= x;
            for (i = 1; i < 8; i = i + 1) tap[i] <= tap[i-1];
            y <= (8'd1 * tap[0]) + (8'd2 * tap[1]) + (8'd3 * tap[2]) + (8'd4 * tap[3]) + (8'd5 * tap[4]) + (8'd6 * tap[5]) + (8'd7 * tap[6]) + (8'd8 * tap[7]);
        end
    end
endmodule