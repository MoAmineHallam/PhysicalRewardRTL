module base__firr6__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] tap [0:5];

always @(posedge clk) begin
    if(!rst_n) begin
        y <= 0;
        for(int i=0; i<6; i=i+1) begin
            tap[i] <= 0;
        end
    end else begin
        tap[0] <= x;
        y <= tap[5]*6 + tap[4]*5 + tap[3]*4 + tap[2]*3 + tap[1]*2 + tap[0]*1;
        for(int i=0; i<5; i=i+1) begin
            tap[i+1] <= tap[i];
        end
    end
end

endmodule