module base__poly7_v4_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 0; // Clear output on reset
    end else begin
        y <= ((((((((x*20)+77)*x+15)*x+31)*x+25)*x+28)*x+45)*x+10) % 65536;
    end
end

endmodule