module base__fir6_8b__g8 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] dline [0:5];
    assign y = (rst_n == 1'b0) ? 16'd0 : 
               (dline[0]*8'd3) + (dline[1]*8'd5) + (dline[2]*8'd7) + (dline[3]*8'd7) + (dline[4]*8'd5) + (dline[5]*8'd3);

    always @(posedge clk) begin
        if (rst_n == 1'b0) begin
            for (int i = 0; i < 6; i = i + 1) begin
                dline[i] <= 8'd0;
            end
        end
        else begin
            for (int i = 5; i > 0; i = i - 1) begin
                dline[i] <= dline[i-1];
            end
            dline[0] <= x;
        end
    end
    
endmodule