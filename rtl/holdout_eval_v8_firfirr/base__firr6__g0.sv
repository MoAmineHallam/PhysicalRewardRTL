module base__firr6__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap [5:0];

    always @ (posedge clk) begin
        if (!rst_n) begin
            y <= 0;
            for (int i = 0; i < 6; i = i + 1) begin
                tap[i] <= 0;
            end
        end else begin
            tap[0] <= x;
            tap[1] <= tap[0];
            tap[2] <= tap[1];
            tap[3] <= tap[2];
            tap[4] <= tap[3];
            tap[5] <= tap[4];

            y <= 8'(tap[0])*8'h01 + 8'(tap[1])*8'h02 + 8'(tap[2])*8'h03 + 8'(tap[3])*8'h04 + 8'(tap[4])*8'h05 + 8'(tap[5])*8'h06;
        end
    end

endmodule