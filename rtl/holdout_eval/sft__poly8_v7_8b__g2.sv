module sft__poly8_v7_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= (((((((((16'd57 * x + 16'd11) * x + 16'd20) * x + 16'd96) * x + 16'd53) * x + 16'd74) * x + 16'd25) * x + 16'd52) * x + 16'd15)) & 16'hFFFF;
    end
endmodule