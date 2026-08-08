module base__firr6__g2(
    input clk,
    input rst_n,
    input [7:0] x,
    output reg [15:0] y
);

reg [7:0] tap [0:5];
integer i;
reg [1:0] rdy;

always @(posedge clk)
    if (!rst_n)
        rdy <= 1'b0;
    else
        rdy <= 1'b1;

always @(posedge clk)
    if (!rst_n || !rdy)
        for (i = 0; i < 6; i = i + 1)
            tap[i] <= 8'd0;
    else
        for (i = 5; i > 0; i = i - 1)
            tap[i] <= tap[i - 1];

`ifdef NOUNROLL
always @(posedge clk) begin
    if (!rst_n || !rdy)
        tap[0] <= 8'd0;
    else
        tap[0] <= x;
end

always @(posedge clk)
    if (!rst_n)
        y <= 16'd0;
    else begin
        y <= 16'd0;
        for (i = 5; i >= 0; i = i - 1)
            y <= y + tap[i] * (i + 1);
    end
`else
    // unrolled versions
always @(posedge clk) begin
    if (!rst_n || !rdy)
        tap[0] <= 8'd0;
    else
        tap[0] <= x;
end

always @(posedge clk) begin
    if (!rst_n)
        y <= 16'd0;
    else
        y <= tap[0] * 9'd1 + tap[1] * 9'd2 + tap[2] * 9'd3 + tap[3] * 9'd4 + tap[4] * 9'd5 + tap[5] * 9'd6;
end

`endif
endmodule