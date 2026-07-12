module base__fir10_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    parameter WIDTH = 16;
    parameter TAPS = 10;

    reg [7:0] delay_line[0:TAPS-1];
    integer i;

    wire [WIDTH-1:0] sum;
    reg [WIDTH-1:0] acc;

    assign sum = (delay_line[0] * 3) +
                 (delay_line[1] * 5) +
                 (delay_line[2] * 7) +
                 (delay_line[3] * 9) +
                 (delay_line[4] * 11) +
                 (delay_line[5] * 11) +
                 (delay_line[6] * 9) +
                 (delay_line[7] * 7) +
                 (delay_line[8] * 5) +
                 (delay_line[9] * 3);

    always @(posedge clk) begin
        if (!rst_n) begin
            acc <= 0;
            for (i = 0; i < TAPS; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
        end
        else begin
            acc <= sum;
            for (i = TAPS-1; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;
        end
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
        end
        else begin
            y <= acc;
        end
    end

endmodule