module base__fir40_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [39:0]; // 40-element delay line
reg [15:0] accumulator;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 0;
        accumulator <= 0;
        for (int i = 0; i < 40; i = i + 1) begin
            delay_line[i] <= 0;
        end
    end else begin
        // Update the delay line and accumulator
        delay_line[0] <= x;
        for (int i = 0; i < 39; i = i + 1) begin
            delay_line[i+1] <= delay_line[i];
        end
        accumulator <= {4'b0, x} * 3 + {4'b0, delay_line[0]} * 5 + {4'b0, delay_line[1]} * 7 +
                       {4'b0, delay_line[2]} * 9 + {4'b0, delay_line[3]} * 11 + {4'b0, delay_line[4]} * 13 +
                       {4'b0, delay_line[5]} * 15 + {4'b0, delay_line[6]} * 17 + {4'b0, delay_line[7]} * 19 +
                       {4'b0, delay_line[8]} * 21 + {4'b0, delay_line[9]} * 23 + {4'b0, delay_line[10]} * 25 +
                       {4'b0, delay_line[11]} * 27 + {4'b0, delay_line[12]} * 29 + {4'b0, delay_line[13]} * 31 +
                       {4'b0, delay_line[14]} * 33 + {4'b0, delay_line[15]} * 35 + {4'b0, delay_line[16]} * 37 +
                       {4'b0, delay_line[17]} * 39 + {4'b0, delay_line[18]} * 41 + {4'b0, delay_line[19]} * 41 +
                       {4'b0, delay_line[20]} * 39 + {4'b0, delay_line[21]} * 37 + {4'b0, delay_line[22]} * 35 +
                       {4'b0, delay_line[23]} * 33 + {4'b0, delay_line[24]} * 31 + {4'b0, delay_line[25]} * 29 +
                       {4'b0, delay_line[26]} * 27 + {4'b0, delay_line[27]} * 25 + {4'b0, delay_line[28]} * 23 +
                       {4'b0, delay_line[29]} * 21 + {4'b0, delay_line[30]} * 19 + {4'b0, delay_line[31]} * 17 +
                       {4'b0, delay_line[32]} * 15 + {4'b0, delay_line[33]} * 13 + {4'b0, delay_line[34]} * 11 +
                       {4'b0, delay_line[35]} * 9 + {4'b0, delay_line[36]} * 7 + {4'b0, delay_line[37]} * 5 +
                       {4'b0, delay_line[38]} * 3;
        y <= accumulator;
    end
end

endmodule