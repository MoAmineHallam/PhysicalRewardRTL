module base__firr10__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] tap [0:9]; // 10-element delay line

integer i;

always @(posedge clk) begin
    if (!rst_n) begin // clear all state
        y <= 0;
        for (i = 0; i < 10; i = i + 1) begin
            tap[i] <= 0;
        end
    end else begin // compute output
        y <= (tap[0] + tap[1]*2 + tap[2]*3 + tap[3]*4 + tap[4]*5 + tap[5]*6 + tap[6]*7 + tap[7]*8 + tap[8]*9 + tap[9]*10) & 16'hFFFF;
        tap[0] <= x;
        for (i = 1; i < 10; i = i + 1) begin
            tap[i] <= tap[i-1];
        end
    end
end

endmodule