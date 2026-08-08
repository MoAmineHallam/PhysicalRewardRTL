module base__fir6_8b__g5 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [5:0];

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (int i = 0; i < 6; i = i + 1) begin
            delay_line[i] <= 8'd0;
        end
        y <= 16'd0;
    end else begin
        // Update delay line
        delay_line[0] <= x;
        for (int i = 1; i < 6; i = i + 1) begin
            delay_line[i] <= delay_line[i-1];
        end

        // Calculate new output
        y <= delay_line[0]*8'd3 + delay_line[1]*8'd5 + delay_line[2]*8'd7 +
             delay_line[3]*8'd7 + delay_line[4]*8'd5 + delay_line[5]*8'd3;
    end
end

endmodule