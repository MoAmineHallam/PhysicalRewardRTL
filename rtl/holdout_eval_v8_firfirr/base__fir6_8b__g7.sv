module base__fir6_8b__g7 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [5:0];
    reg [7:0] coefficient [5:0];

    initial begin
        for (int i = 0; i < 6; i = i + 1) begin
            coefficient[i] = 0;
        end
        coefficient[0] = 3;
        coefficient[1] = 5;
        coefficient[2] = 7;
        coefficient[3] = 7;
        coefficient[4] = 5;
        coefficient[5] = 3;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 0;
            for (int i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 0;
            end
        end else begin
            y <= (coefficient[0] * delay_line[0]) +
                 (coefficient[1] * delay_line[1]) +
                 (coefficient[2] * delay_line[2]) +
                 (coefficient[3] * delay_line[3]) +
                 (coefficient[4] * delay_line[4]) +
                 (coefficient[5] * delay_line[5]);

            for (int i = 5; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i - 1];
            end
            delay_line[0] <= x;
        end
    end
endmodule