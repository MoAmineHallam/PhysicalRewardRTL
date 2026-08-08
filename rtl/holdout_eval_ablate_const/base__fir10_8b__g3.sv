module base__fir10_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] dl [9:0]; // Delay line

always @(posedge clk) begin
    if (!rst_n) begin
        y <= 0;
        for (int i = 0; i < 10; i = i + 1) begin
            dl[i] <= 0;
        end
    end else begin
        dl[0] <= x;
        for (int i = 9; i >= 1; i = i - 1) begin
            dl[i] <= dl[i-1];
        end

        y[15:0] <= (dl[0]*3) + 
                   (dl[1]*5) + 
                   (dl[2]*7) + 
                   (dl[3]*9) + 
                   (dl[4]*11) + 
                   (dl[5]*11) + 
                   (dl[6]*9) + 
                   (dl[7]*7) + 
                   (dl[8]*5) + 
                   (dl[9]*3);
    end
end

endmodule