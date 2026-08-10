module base__firr36__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap [0:35];
    integer k;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 0;
            for (k = 0; k < 36; k = k + 1) begin
                tap[k] <= 0;
            end
        end
        else begin
            y <= ( (36'd1 * tap[0]) +
                    (36'd2 * tap[1]) +
                    (36'd3 * tap[2]) +
                    (36'd4 * tap[3]) +
                    (36'd5 * tap[4]) +
                    (36'd6 * tap[5]) +
                    (36'd7 * tap[6]) +
                    (36'd8 * tap[7]) +
                    (36'd9 * tap[8]) +
                    (36'd10 * tap[9]) +
                    (36'd11 * tap[10]) +
                    (36'd12 * tap[11]) +
                    (36'd13 * tap[12]) +
                    (36'd14 * tap[13]) +
                    (36'd15 * tap[14]) +
                    (36'd16 * tap[15]) +
                    (36'd17 * tap[16]) +
                    (36'd18 * tap[17]) +
                    (36'd19 * tap[18]) +
                    (36'd20 * tap[19]) +
                    (36'd21 * tap[20]) +
                    (36'd22 * tap[21]) +
                    (36'd23 * tap[22]) +
                    (36'd24 * tap[23]) +
                    (36'd25 * tap[24]) +
                    (36'd26 * tap[25]) +
                    (36'd27 * tap[26]) +
                    (36'd28 * tap[27]) +
                    (36'd29 * tap[28]) +
                    (36'd30 * tap[29]) +
                    (36'd31 * tap[30]) +
                    (36'd32 * tap[31]) +
                    (36'd33 * tap[32]) +
                    (36'd34 * tap[33]) +
                    (36'd35 * tap[34]) +
                    (36'd36 * tap[35])
                  ) & 16'hFFFF;
            for (k = 35; k > 0; k = k - 1) begin
                tap[k] <= tap[k-1];
            end
            tap[0] <= x;
        end
    end

endmodule