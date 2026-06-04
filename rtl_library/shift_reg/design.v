// Golden reference: 8-bit serial-in parallel-out shift register
module shift_reg (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       en,
    input  wire       sin,
    output wire [7:0] q
);
    reg [7:0] sr;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            sr <= 8'b0;
        else if (en)
            sr <= {sr[6:0], sin};
    end

    assign q = sr;
endmodule
