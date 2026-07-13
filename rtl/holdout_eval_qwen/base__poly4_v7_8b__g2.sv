module base__poly4_v7_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg  [15:0] temp;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 16'b0;
        temp <= 16'b0;
    end else begin
        // Initialize temp with the highest coefficient
        temp <= 24;
        
        // Horner's method for evaluating the polynomial
        temp = temp * x + 36;
        temp = temp * x + 17;
        temp = temp * x + 21;
        temp = temp * x + 50;
        
        // Keep only the low 16 bits of the result
        temp = temp & 16'hFFFF;
        
        // Assign the result to y
        y <= temp;
    end
end

endmodule