module poly6_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [15:0] t0;
    reg [15:0] t1;
    reg [15:0] t2;
    reg [15:0] t3;
    reg [15:0] t4;
    reg [15:0] t5;
    reg [15:0] t6;
    reg [7:0] xd1;
    reg [7:0] xd2;
    reg [7:0] xd3;
    reg [7:0] xd4;
    reg [7:0] xd5;
    reg [7:0] xd6;
    always @(posedge clk) begin
        if (!rst_n) begin t0 <= 16'd0; t1 <= 16'd0; t2 <= 16'd0; t3 <= 16'd0; t4 <= 16'd0; t5 <= 16'd0; t6 <= 16'd0; xd1 <= 8'd0; xd2 <= 8'd0; xd3 <= 8'd0; xd4 <= 8'd0; xd5 <= 8'd0; xd6 <= 8'd0; y <= 16'd0; end
        else begin
            t0 <= 16'd1;
            xd1 <= x;
            t1 <= t0 * xd1 + 16'd3;
            xd2 <= xd1;
            t2 <= t1 * xd2 + 16'd5;
            xd3 <= xd2;
            t3 <= t2 * xd3 + 16'd7;
            xd4 <= xd3;
            t4 <= t3 * xd4 + 16'd9;
            xd5 <= xd4;
            t5 <= t4 * xd5 + 16'd11;
            xd6 <= xd5;
            t6 <= t5 * xd6 + 16'd13;
            y <= t6;
        end
    end
endmodule