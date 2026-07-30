module base__fir6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line[0:5];
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 8'b0;
            end
            y <= 16'b0;
        end else begin
            // shift input into delay line
            delay_line[5] <= delay_line[4];
            delay_line[4] <= delay_line[3];
            delay_line[3] <= delay_line[2];
            delay_line[2] <= delay_line[1];
            delay_line[1] <= delay_line[0];
            delay_line[0] <= x;
            
            // calculate output
            y <= (delay_line[5] * 8'h03) + (delay_line[4] * 8'h05) + (delay_line[3] * 8'h07) + (delay_line[2] * 8'h07) + (delay_line[1] * 8'h05) + (delay_line[0] * 8'h03);
        end
    end

endmodule