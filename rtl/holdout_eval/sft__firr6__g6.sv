module sft__firr6__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:5];
    integer     i;
    reg  [23:0] acc;
    always @(*) acc = xs[0]*1 + xs[1]*2 + xs[2]*3 + xs[3]*4 + xs[4]*5 + xs[5]*6;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 6; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 6; i = i + 1) xs[i] <= xs[i-1];
            y <= acc[15:0];
        end
    end
endmodule