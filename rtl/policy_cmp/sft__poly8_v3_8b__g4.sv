module sft__poly8_v3_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= ((((((((16'd31 * x + 16'd63) * x + 16'd52) * x + 16'd34) * x + 16'd17) * x + 16'd35) * x + 16'd46) * x + 16'd92) * x + 16'd14) & 16'hFFFF;
    end
endmodule