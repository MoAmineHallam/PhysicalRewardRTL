// Clock divider / enable generator: en pulses once every 4 clocks.
// cnt free-runs 0->1->2->3->0. en is registered (cnt==3) from previous cycle.
module clk_div4 (
    input  wire       clk,
    input  wire       rst_n,
    output reg  [1:0] cnt,
    output reg        en
);
    always @(posedge clk) begin
        if (!rst_n) begin
            cnt <= 2'd0;
            en  <= 1'b0;
        end else begin
            en  <= (cnt == 2'd3);
            cnt <= cnt + 2'd1;
        end
    end
endmodule
