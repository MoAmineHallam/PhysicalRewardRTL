module base__fir6_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [0:5];

always @(posedge clk) begin
    if (!rst_n) begin
        y <= 0;
        for (int i = 0; i < 6; i = i + 1) begin
            delay_line[i] <= 0;
        end
    end
    else begin
        // Shift data in delay line
        delay_line[0] <= x;
        for (int i = 1; i < 6; i = i + 1) begin
            delay_line[i] <= delay_line[i-1];
        end

        // Calculate output
        y <= (delay_line[0] * 3) + (delay_line[1] * 5) + (delay_line[2] * 7) + (delay_line[3] * 7) + (delay_line[4] * 5) + (delay_line[5] * 3);
    end
end

endmodule