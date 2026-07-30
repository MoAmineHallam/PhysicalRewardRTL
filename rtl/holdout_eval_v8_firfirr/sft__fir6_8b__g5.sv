module sft__fir6_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  mem0;
    reg  [7:0]  mem1;
    reg  [7:0]  mem2;
    reg  [7:0]  mem3;
    reg  [7:0]  mem4;
    reg  [7:0]  mem5;
    wire [15:0] acc = 8'd3 * mem0 + 8'd5 * mem1 + 8'd7 * mem2 + 8'd7 * mem3 + 8'd5 * mem4 + 8'd3 * mem5;
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16'd0;
            mem0 <= 8'd0;
            mem1 <= 8'd0;
            mem2 <= 8'd0;
            mem3 <= 8'd0;
            mem4 <= 8'd0;
            mem5 <= 8'd0;
        end else begin
            y <= acc;
            mem0 <= x;
            mem1 <= mem0;
            mem2 <= mem1;
            mem3 <= mem2;
            mem4 <= mem3;
            mem5 <= mem4;
        end
    end
endmodule