// 4-bit up/down counter. dir=0: count up, dir=1: count down.
// Input: dir=cnt[0]. Period=32 (16 up + 16 down alternating via cnt[4]).
module updown_counter (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       dir,
    output reg  [3:0] count
);
    always @(posedge clk) begin
        if (!rst_n)   count <= 4'd0;
        else if (dir) count <= count - 4'd1;
        else          count <= count + 4'd1;
    end
endmodule
