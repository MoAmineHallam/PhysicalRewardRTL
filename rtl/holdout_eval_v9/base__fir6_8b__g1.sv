module base__fir6_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [5:0];
    reg [15:0] acc;
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 0;
            end
            acc <= 0;
            y <= 0;
        end
        else begin
            delay_line[0] <= x;
            for (i = 0; i < 5; i = i + 1) begin
                delay_line[i+1] <= delay_line[i];
            end

            acc <= delay_line[0]*3 + delay_line[1]*5 + delay_line[2]*7 + delay_line[3]*7 + delay_line[4]*5 + delay_line[5]*3;
            y <= acc;
        end
    end

endmodule