module base__fir6_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [5:0]; // 6-element delay line
reg [15:0] acc; // accumulator for sum of products

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 0;
        acc <= 0;
        for (int i = 0; i < 6; i = i + 1) begin
            delay_line[i] <= 0;
        end
    end
    else begin
        acc <= (x*3) + (delay_line[0]*5) + (delay_line[1]*7) + (delay_line[2]*7) + (delay_line[3]*5) + (delay_line[4]*3);
        y[15:0] <= acc[15:0];
        for (int i = 4; i >= 0; i = i - 1) begin
            delay_line[i+1] <= delay_line[i];
        end
        delay_line[0] <= x;
    end
end

endmodule