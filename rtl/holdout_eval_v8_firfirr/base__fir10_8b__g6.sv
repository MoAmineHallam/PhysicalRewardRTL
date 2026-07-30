module base__fir10_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [9:0]; // 10-element delay line
reg [15:0] acc; // accumulator for output
integer i; // used in the for loop

always @(posedge clk) begin
    if (!rst_n) begin
        y <= 0;
        for (i = 0; i < 10; i = i + 1) begin
            delay_line[i] <= 0;
        end
    end
    else begin
        delay_line[0] <= x; // input x is at the 0th element of the delay line
        for (i = 1; i < 10; i = i + 1) begin
            delay_line[i] <= delay_line[i-1]; // shift the delay line
        end
        acc <= (delay_line[0]*3) +
               (delay_line[1]*5) +
               (delay_line[2]*7) +
               (delay_line[3]*9) +
               (delay_line[4]*11) +
               (delay_line[5]*11) +
               (delay_line[6]*9) +
               (delay_line[7]*7) +
               (delay_line[8]*5) +
               (delay_line[9]*3);
        y <= acc[15:0];
    end
end

endmodule