module base__firr36__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [0:35];
    integer i;

    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16'd0;
            for (i = 0; i < 36; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
        end else begin
            y <= {16'd0, delay_line[0]} +
                 delay_line[1]*8'd2 +
                 delay_line[2]*8'd3 +
                 delay_line[3]*8'd4 +
                 delay_line[4]*8'd5 +
                 delay_line[5]*8'd6 +
                 delay_line[6]*8'd7 +
                 delay_line[7]*8'd8 +
                 delay_line[8]*8'd9 +
                 delay_line[9]*8'd10 +
                 delay_line[10]*8'd11 +
                 delay_line[11]*8'd12 +
                 delay_line[12]*8'd13 +
                 delay_line[13]*8'd14 +
                 delay_line[14]*8'd15 +
                 delay_line[15]*8'd16 +
                 delay_line[16]*8'd17 +
                 delay_line[17]*8'd18 +
                 delay_line[18]*8'd19 +
                 delay_line[19]*8'd20 +
                 delay_line[20]*8'd21 +
                 delay_line[21]*8'd22 +
                 delay_line[22]*8'd23 +
                 delay_line[23]*8'd24 +
                 delay_line[24]*8'd25 +
                 delay_line[25]*8'd26 +
                 delay_line[26]*8'd27 +
                 delay_line[27]*8'd28 +
                 delay_line[28]*8'd29 +
                 delay_line[29]*8'd30 +
                 delay_line[30]*8'd31 +
                 delay_line[31]*8'd32 +
                 delay_line[32]*8'd33 +
                 delay_line[33]*8'd34 +
                 delay_line[34]*8'd35 +
                 delay_line[35]*8'd36;
            for (i = 35; i > 0; i = i - 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            delay_line[0] <= x;
        end
    end

endmodule