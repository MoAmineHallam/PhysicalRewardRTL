module base__fir18_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay[0:17];
    integer i;
    wire [63:0] prod; // 18 taps in, 8 bit input, 16 bit output

    assign prod = (
        (delay[17] * 3) +
        (delay[16] * 5) +
        (delay[15] * 7) +
        (delay[14] * 9) +
        (delay[13] * 11) +
        (delay[12] * 13) +
        (delay[11] * 15) +
        (delay[10] * 17) +
        (delay[9] * 19) +
        (delay[8] * 19) +
        (delay[7] * 17) +
        (delay[6] * 15) +
        (delay[5] * 13) +
        (delay[4] * 11) +
        (delay[3] * 9) +
        (delay[2] * 7) +
        (delay[1] * 5) +
        (delay[0] * 3)
    );

    always @(posedge clk, negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1) begin
                delay[i] <= 0;
            end
            y <= 0;
        end
        else begin
            delay[0] <= x;
            for (i = 1; i < 18; i = i + 1) begin
                delay[i] <= delay[i-1];
            end
            y <= prod[15:0];
        end
    end

endmodule