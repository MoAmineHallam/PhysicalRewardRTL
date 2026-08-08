module sft__poly8_v7_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [15:0] t0;
    reg  [15:0] t1;
    reg  [15:0] t2;
    reg  [15:0] t3;
    reg  [15:0] t4;
    reg  [15:0] t5;
    reg  [15:0] t6;
    reg  [15:0] t7;
    reg  [15:0] t8;
    always @(posedge clk) begin
        if (!rst_n) begin y <= 16'd0; t0 <= 16'd0; t1 <= 16'd0; t2 <= 16'd0; t3 <= 16'd0; t4 <= 16'd0; t5 <= 16'd0; t6 <= 16'd0; t7 <= 16'd0; t8 <= 16'd0; end
        else begin
            y <= (((((((((16'd57 * x + 16'd11) * x + 16'd20) * x + 16'd96) * x + 16'd53) * x + 16'd74) * x + 16'd25) * x + 16'd52) * x + 16'd15)) & 16'hFFFF;
            t0 <= (16'd57 * x) & 16'hFFFF;
            t1 <= (16'd57 * x * x + 16'd11) & 16'hFFFF;
            t2 <= (16'd57 * x * x * x + 16'd20 * x + 16'd96) & 16'hFFFF;
            t3 <= (16'd57 * x * x * x * x + 16'd20 * x * x + 16'd96 * x + 16'd53) & 16'hFFFF;
            t4 <= (16'd57 * x * x * x * x * x + 16'd20 * x * x * x + 16'd96 * x * x + 16'd53 * x + 16'd74) & 16'hFFFF;
            t5 <= (16'd57 * x * x * x * x * x * x + 16'd20 * x * x * x * x + 16'd96 * x * x * x + 16'd53 * x * x + 16'd74 * x + 16'd25) & 16'hFFFF;
            t6 <= (16'd57 * x * x * x * x * x * x * x + 16'd20 * x * x * x * x * x + 16'd96 * x * x * x * x + 16'd53 * x * x * x + 16'd74 * x * x + 16'd25 * x + 16'd52) & 16'hFFFF;
            t7 <= (16'd57 * x * x * x * x * x * x * x * x + 16'd20 * x * x * x * x * x * x + 16'd96 * x * x * x * x * x + 16'd53 * x * x * x * x + 16'd74 * x * x * x + 16'd25 * x * x + 16'd52 * x + 16'd15) & 16'hFFFF;
            t8 <= (16'd57 * x * x * x * x * x * x * x * x * x + 16'd20 * x * x * x * x * x * x * x + 16'd96 * x * x * x * x * x * x + 16'd53 * x * x * x * x * x + 16'd74 * x * x * x * x + 16'd25 * x * x * x + 16'd52 * x * x + 16'd15 * x + 16'd0) & 16'hFFFF;
        end
    end
endmodule