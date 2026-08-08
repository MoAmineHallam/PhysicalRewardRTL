module base__fir18_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    parameter SIZE = 18;

    reg [7:0] delay_line [SIZE-1:0];
    integer i;

    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16'h0000;
            for (i=0; i<SIZE; i=i+1) begin
                delay_line[i] <= 8'h00;
            end
        end else begin
            y <= (delay_line[0]*3) + (delay_line[1]*5) + (delay_line[2]*7) +
                 (delay_line[3]*9) + (delay_line[4]*11) + (delay_line[5]*13) +
                 (delay_line[6]*15) + (delay_line[7]*17) + (delay_line[8]*19) +
                 (delay_line[9]*19) + (delay_line[10]*17) + (delay_line[11]*15) +
                 (delay_line[12]*13) + (delay_line[13]*11) + (delay_line[14]*9) +
                 (delay_line[15]*7) + (delay_line[16]*5) + (delay_line[17]*3);

            for (i=SIZE-1; i>0; i=i-1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;
        end
    end
endmodule