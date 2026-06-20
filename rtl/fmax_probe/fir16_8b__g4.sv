module fir16_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:15];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 16; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 16; i = i + 1) xs[i] <= xs[i-1];
            y <= xs[0]*8'd3 + xs[1]*8'd7 + xs[2]*8'd12 + xs[3]*8'd19 + xs[4]*8'd27 + xs[5]*8'd34 + xs[6]*8'd40 + xs[7]*8'd43 + xs[8]*8'd43 + xs[9]*8'd40 + xs[10]*8'd34 + xs[11]*8'd27 + xs[12]*8'd19 + xs[13]*8'd12 + xs[14]*8'd7 + xs[15]*8'd3;
        end
    end
endmodule