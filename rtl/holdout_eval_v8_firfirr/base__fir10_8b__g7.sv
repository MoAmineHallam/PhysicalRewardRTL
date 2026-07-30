module base__fir10_8b__g7 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:9];
    integer i;
    reg [7:0] coefficient [0:9];
    
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1) begin
                delay_line[i] <= 0;
                coefficient[i] <= 0;
            end
            y <= 0;
        end else begin
            for (i = 0; i < 9; i = i +1) begin
                delay_line[i] <= delay_line[i+1];
            end
            delay_line[9] <= x;
            
            coefficient[0] <= 3;
            coefficient[1] <= 5;
            coefficient[2] <= 7;
            coefficient[3] <= 9;
            coefficient[4] <= 11;
            coefficient[5] <= 11;
            coefficient[6] <= 9;
            coefficient[7] <= 7;
            coefficient[8] <= 5;
            coefficient[9] <= 3;
            
            y <= delay_line[0]*coefficient[0] + delay_line[1]*coefficient[1] + delay_line[2]*coefficient[2] 
                + delay_line[3]*coefficient[3] + delay_line[4]*coefficient[4] + delay_line[5]*coefficient[5] 
                + delay_line[6]*coefficient[6] + delay_line[7]*coefficient[7] + delay_line[8]*coefficient[8] 
                + delay_line[9]*coefficient[9];
        end
    end

endmodule