module sft__poly8_v6_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= ((((((((16'd92 * x + 16'd96) * x + 16'd7) * x + 16'd62) * x + 16'd54) * x + 16'd61) * x + 16'd77) * x + 16'd51) * x + 16'd45) & 16'hFFFF;
    end
endmodule