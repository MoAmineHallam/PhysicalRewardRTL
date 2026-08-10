module base__fir10_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:9] /* synthesis syn_srlstyle="no" */;
    reg [15:0] acc;
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'h0000;
            for (i = 0; i < 10; i = i + 1) begin
                delay_line[i] <= 8'h00;
            end
            acc <= 16'h0000;
        end
        else begin
            delay_line[0] <= x;
            for (i = 1; i < 10; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            acc <= x * 8'h03 + 
                  delay_line[0] * 8'h05 +
                  delay_line[1] * 8'h07 +
                  delay_line[2] * 8'h09 +
                  delay_line[3] * 8'h0B +
                  delay_line[4] * 8'h0B +
                  delay_line[5] * 8'h09 +
                  delay_line[6] * 8'h07 +
                  delay_line[7] * 8'h05 +
                  delay_line[8] * 8'h03;
            y <= acc;
        end
    end

endmodule