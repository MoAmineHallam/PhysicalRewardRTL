module sft__fir6_8b__g4 (
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
    reg  [23:0] acc;
    // One register per combinational stage: pipeline the MAC cone strictly.
    always @(*) acc = 8'd3 * mem0 + 8'd5 * mem1 + 8'd7 * mem2 + 8'd7 * mem3 + 8'd5 * mem4 + 8'd3 * mem5;
    always @(posedge clk) begin
        if (!rst_n) begin
            y<=0; mem0<=0; mem1<=0; mem2<=0; mem3<=0; mem4<=0; mem5<=0;
        end else begin
            y <= acc[15:0];
            mem0 <= x;
            mem1 <= mem0;
            mem2 <= mem1;
            mem3 <= mem2;
            mem4 <= mem3;
            mem5 <= mem4;
        end
    end
endmodule