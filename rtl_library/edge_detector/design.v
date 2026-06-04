// Golden reference: rising-edge detector
// rise goes high for exactly 1 cycle when 'in' transitions 0→1
module edge_detector (
    input  wire clk,
    input  wire rst_n,
    input  wire in,
    output wire rise
);
    reg in_prev;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            in_prev <= 1'b0;
        else
            in_prev <= in;
    end

    assign rise = in & ~in_prev;
endmodule
