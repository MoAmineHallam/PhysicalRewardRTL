module base__poly7_v2_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [15:0] coef [0:7];
    
    assign coef[0] = 72;
    assign coef[1] = 67;
    assign coef[2] = 4;
    assign coef[3] = 10;
    assign coef[4] = 88;
    assign coef[5] = 75;
    assign coef[6] = 86;
    assign coef[7] = 39;
    
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
        end else begin
            y <= coef[7] + coef[6]*x + coef[5]*x*x + coef[4]*x*x*x + coef[3]*x*x*x*x + coef[2]*x*x*x*x*x + coef[1]*x*x*x*x*x*x + coef[0]*x*x*x*x*x*x*x;
        end
    end

endmodule