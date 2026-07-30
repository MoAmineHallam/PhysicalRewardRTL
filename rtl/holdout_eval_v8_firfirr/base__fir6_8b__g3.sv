module base__fir6_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [5:0];
    reg [31:0] acc;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 0;
            acc <= 0;
            for (int i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 0;
            end
        end
        else begin
            // Shift the delay line
            for (int i = 4; i >= 0; i = i - 1) begin
                delay_line[i+1] <= delay_line[i];
            end
            delay_line[0] <= x;
            
            // Calculate the sum of products
            acc <= delay_line[0]*3 + 
                   delay_line[1]*5 + 
                   delay_line[2]*7 + 
                   delay_line[3]*7 + 
                   delay_line[4]*5 + 
                   delay_line[5]*3;
            
            // Output the low 16 bits of the sum of products
            y <= acc[15:0];
        end
    end

endmodule