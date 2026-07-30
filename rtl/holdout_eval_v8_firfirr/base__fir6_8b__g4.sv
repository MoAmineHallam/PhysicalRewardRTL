module base__fir6_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] x_delay[0:5];
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i=0; i<6; i=i+1) begin
                x_delay[i] <= 8'b0;
            end
            y <= 16'b0;
        end
        else begin
            for (i=5; i>0; i=i-1) begin
                x_delay[i] <= x_delay[i-1];
            end
            x_delay[0] <= x;
            y <= (x_delay[0]*3) + (x_delay[1]*5) + (x_delay[2]*7) + (x_delay[3]*7) + (x_delay[4]*5) + (x_delay[5]*3);
        end
    end

endmodule