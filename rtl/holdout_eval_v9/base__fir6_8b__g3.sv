module base__fir6_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] shift_reg [0:5];
reg [15:0] acc;

integer i;

always @(posedge clk) begin
    if (!rst_n) begin
        y <= 0;
        acc <= 0;
        for (i = 0; i < 6; i = i + 1) begin
            shift_reg[i] <= 0;
        end
    end else begin
        shift_reg[0] <= x;
        for (i = 1; i < 6; i = i + 1) begin
            shift_reg[i] <= shift_reg[i-1];
        end
        
        acc <= (3 * shift_reg[0]) + (5 * shift_reg[1]) + (7 * shift_reg[2]) + (7 * shift_reg[3]) + (5 * shift_reg[4]) + (3 * shift_reg[5]);
        
        y <= acc;
    end
end

endmodule