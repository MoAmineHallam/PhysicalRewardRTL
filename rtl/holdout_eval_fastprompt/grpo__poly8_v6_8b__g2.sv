module grpo__poly8_v6_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [15:0] t0;
    reg [15:0] t1;
    reg [15:0] t2;
    reg [15:0] t3;
    reg [15:0] t4;
    reg [15:0] t5;
    reg [15:0] t6;
    reg [15:0] t7;
    reg [15:0] t8;
    always @(posedge clk) begin
        if (!rst_n) begin y <= 16'd0; t0 <= 16'd0; t1 <= 16'd0; t2 <= 16'd0; t3 <= 16'd0; t4 <= 16'd0; t5 <= 16'd0; t6 <= 16'd0; t7 <= 16'd0; t8 <= 16'd0; end
        else        begin y <= t8;
        t8 <= (((((((((16'd92 * x + 16'd96) * x + 16'd7) * x + 16'd62) * x + 16'd54) * x + 16'd61) * x + 16'd77) * x + 16'd51) * x + 16'd45)) & 16'hFFFF;
        end
    end
endmodule