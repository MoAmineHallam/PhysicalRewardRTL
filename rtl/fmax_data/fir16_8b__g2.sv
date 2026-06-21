module fir16_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  mem [0:15];
    integer     i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 16; i = i + 1) mem[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            mem[0] <= x;
            for (i = 1; i < 16; i = i + 1) mem[i] <= mem[i-1];
            y <= 8'd3 * mem[0] + 8'd7 * mem[1] + 8'd12 * mem[2] + 8'd19 * mem[3] + 8'd27 * mem[4] + 8'd34 * mem[5] + 8'd40 * mem[6] + 8'd43 * mem[7] + 8'd43 * mem[8] + 8'd40 * mem[9] + 8'd34 * mem[10] + 8'd27 * mem[11] + 8'd19 * mem[12] + 8'd12 * mem[13] + 8'd7 * mem[14] + 8'd3 * mem[15];
        end
    end
endmodule