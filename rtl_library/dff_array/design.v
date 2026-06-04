// Golden reference: 8-bit D flip-flop array with synchronous enable
module dff_array (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       en,
    input  wire [7:0] d,
    output reg  [7:0] q
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            q <= 8'b0;
        else if (en)
            q <= d;
    end
endmodule
