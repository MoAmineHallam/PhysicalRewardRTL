module base__fir6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:5];
    reg [15:0] accumulator;
    wire [15:0] tap1, tap2, tap3, tap4, tap5, tap6;
    
    assign tap1 = delay_line[0] * 3;
    assign tap2 = delay_line[1] * 5;
    assign tap3 = delay_line[2] * 7;
    assign tap4 = delay_line[3] * 7;
    assign tap5 = delay_line[4] * 5;
    assign tap6 = delay_line[5] * 3;
    
    always @(posedge clk, negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'b0;
            accumulator <= 16'b0;
            for (int i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 8'b0;
            end
        end
        else begin
            accumulator <= tap1 + tap2 + tap3 + tap4 + tap5 + tap6;
            delay_line[0] <= x;
            y <= accumulator;
            for (int i = 1; i < 6; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
        end
    end
endmodule