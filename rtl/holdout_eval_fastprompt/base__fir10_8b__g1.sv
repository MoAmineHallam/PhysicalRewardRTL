module base__fir10_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line [9:0];
reg [15:0] pipeline_reg [3:0];

always @(posedge clk) begin
    if (!rst_n) begin
        y <= 16'd0;
        for (int i = 0; i < 10; i = i + 1) begin
            delay_line[i] <= 8'd0;
        end
        for (int i = 0; i < 4; i = i + 1) begin
            pipeline_reg[i] <= 16'd0;
        end
    end
    else begin
        // Update delay line
        delay_line[0] <= x;
        for (int i = 9; i > 0; i = i - 1) begin
            delay_line[i] <= delay_line[i-1];
        end
        
        // Compute FIR output
        pipeline_reg[0] <= (delay_line[0]*3) + (delay_line[1]*5) + (delay_line[2]*7) +
                           (delay_line[3]*9) + (delay_line[4]*11) + (delay_line[5]*11) +
                           (delay_line[6]*9) + (delay_line[7]*7) + (delay_line[8]*5) +
                           (delay_line[9]*3);
        for (int i = 3; i > 0; i = i - 1) begin
            pipeline_reg[i] <= pipeline_reg[i-1];
        end
        y <= pipeline_reg[3];
    end
end

endmodule