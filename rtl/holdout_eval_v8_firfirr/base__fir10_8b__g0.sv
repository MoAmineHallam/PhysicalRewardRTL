module base__fir10_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:9];
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // clear state on reset
            for (i = 0; i < 10; i = i + 1) begin
                delay_line[i] <= 0;
            end
            y <= 0;
        end else begin
            // shift in new sample
            for (i = 0; i < 9; i = i + 1) begin
                delay_line[i] <= delay_line[i+1];
            end
            delay_line[9] <= x;

            // calculate output
            y <= delay_line[0]*3 + delay_line[1]*5 + delay_line[2]*7 + delay_line[3]*9 + delay_line[4]*11 + delay_line[5]*11 + delay_line[6]*9 + delay_line[7]*7 + delay_line[8]*5 + delay_line[9]*3;
        end
    end

endmodule