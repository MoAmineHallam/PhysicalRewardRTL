module base__firr36__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] delay_line[36];
reg [15:0] accum;
integer i;

always @(negedge rst_n or posedge clk) begin
    if(!rst_n) begin
        for(i = 0; i < 36; i = i + 1) begin
            delay_line[i] <= 8'd0;
        end
        accum <= 16'd0;
        y <= 16'd0;
    end else begin
        for(i = 35; i > 0; i = i - 1) begin
            delay_line[i] <= delay_line[i-1];
        end
        delay_line[0] <= x;
        accum <= delay_line[0]*(36'd1) + delay_line[1]*(36'd2) + delay_line[2]*(36'd3) + delay_line[3]*(36'd4) + delay_line[4]*(36'd5) + delay_line[5]*(36'd6) + delay_line[6]*(36'd7) + delay_line[7]*(36'd8) + delay_line[8]*(36'd9) + delay_line[9]*(36'd10) + delay_line[10]*(36'd11) + delay_line[11]*(36'd12) + delay_line[12]*(36'd13) + delay_line[13]*(36'd14) + delay_line[14]*(36'd15) + delay_line[15]*(36'd16) + delay_line[16]*(36'd17) + delay_line[17]*(36'd18) + delay_line[18]*(36'd19) + delay_line[19]*(36'd20) + delay_line[20]*(36'd21) + delay_line[21]*(36'd22) + delay_line[22]*(36'd23) + delay_line[23]*(36'd24) + delay_line[24]*(36'd25) + delay_line[25]*(36'd26) + delay_line[26]*(36'd27) + delay_line[27]*(36'd28) + delay_line[28]*(36'd29) + delay_line[29]*(36'd30) + delay_line[30]*(36'd31) + delay_line[31]*(36'd32) + delay_line[32]*(36'd33) + delay_line[33]*(36'd34) + delay_line[34]*(36'd35) + delay_line[35]*(36'd36);
        y <= accum[15:0];
    end
end

endmodule