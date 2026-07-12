module base__fir18_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [17:0]; // 18-element delay line

    integer tap_i;

    always @(negedge rst_n or posedge clk) begin
        if (!rst_n) begin
            for (tap_i=0; tap_i<=17; tap_i=tap_i+1) begin
                delay_line[tap_i] <= 8'b0;
            end
            y <= 16'b0;
        end
        else begin
            // shift delay line
            for (tap_i=0; tap_i<=17; tap_i=tap_i+1) begin
                delay_line[tap_i] <= delay_line[tap_i+1];
            end
            // add x to delay_line[17]
            delay_line[17] <= x;

            // calculate sum of products
            y <= (delay_line[0]*3)+(delay_line[1]*5)+(delay_line[2]*7)+(delay_line[3]*9)+(delay_line[4]*11)+(delay_line[5]*13)+(delay_line[6]*15)+(delay_line[7]*17)+(delay_line[8]*19)+(delay_line[9]*19)+(delay_line[10]*17)+(delay_line[11]*15)+(delay_line[12]*13)+(delay_line[13]*11)+(delay_line[14]*9)+(delay_line[15]*7)+(delay_line[16]*5)+(delay_line[17]*3);
        end
    end
endmodule