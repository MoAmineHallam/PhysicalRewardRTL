module sft__fir6_8b__g10 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs [0:5];
    reg  [15:0] y2;
    reg  [15:0] y3;
    reg  [15:0] y4;
    reg  [15:0] y5;
    reg  [15:0] y6;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (int i = 0; i < 6; i = i + 1) xs[i] <= 8'd0;
            y <= 16'd0;
            y2 <= 16'd0;
            y3 <= 16'd0;
            y4 <= 16'd0;
            y5 <= 16'd0;
            y6 <= 16'd0;
        end else begin
            xs[0] <= x;
            for (int i = 1; i < 6; i = i + 1) xs[i] <= xs[i-1];
            y  <= 16'd3*xs[0] + 16'd5*xs[1] + 16'd7*xs[2] + 16'd7*xs[3] + 16'd5*xs[4] + 16'd3*xs[5];
            y2 <= 16'd3*xs[1] + 16'd5*xs[2] + 16'd7*xs[3] + 16'd7*xs[4] + 16'd5*xs[5] + 16'd3*xs[0];
            y3 <= 16'd3*xs[2] + 16'd5*xs[3] + 16'd7*xs[4] + 16'd7*xs[5] + 16'd5*xs[0] + 16'd3*xs[1];
            y4 <= 16'd3*xs[3] + 16'd5*xs[4] + 16'd7*xs[5] + 16'd7*xs[0] + 16'd5*xs[1] + 16'd3*xs[2];
            y5 <= 16'd3*xs[4] + 16'd5*xs[5] + 16'd7*xs[0] + 16'd7*xs[1] + 16'd5*xs[2] + 16'd3*xs[3];
            y6 <= 16'd3*xs[5] + 16'd5*xs[0] + 16'd7*xs[1] + 16'd7*xs[2] + 16'd5*xs[3] + 16'd3*xs[4];
        end
    end
    // The cone cone (register-to-register path independent)
    wire [31:0] acc = 32'd3*xs[0] + 32'd5*xs[1] + 32'd7*xs[2] + 32'd7*xs[3] + 32'd5*xs[4] + 32'd3*xs[5];
    always @(posedge clk) begin
        y <= acc[15:0];
    end
endmodule