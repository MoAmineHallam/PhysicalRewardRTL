module base__fir6_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [0:5];

integer i;

always @ (posedge clk, negedge rst_n) begin
    if (~rst_n) begin
        for (i = 0; i < 6; i = i + 1) begin
            delay_line[i] <= 8'b0;
        end
        y <= 16'b0;
    end else begin
        for (i = 4; i >= 0; i = i - 1) begin
            delay_line[i+1] <= delay_line[i];
        end
        delay_line[0] <= x;
        y <= delay_line[0]*3 +
             delay_line[1]*5 +
             delay_line[2]*7 +
             delay_line[3]*7 +
             delay_line[4]*5 +
             delay_line[5]*3;
    end
end

endmodule