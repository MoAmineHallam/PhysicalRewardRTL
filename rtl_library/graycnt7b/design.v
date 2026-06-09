// 7-bit Gray-code counter (output is Gray of internal binary count).
module graycnt7b (
    input  wire clk, rst_n,
    output reg  [6:0] gray
);
    reg [6:0] bin;
    always @(posedge clk) begin
        if (!rst_n) begin bin <= 0; gray <= 0; end
        else begin
            bin  <= bin + 1'b1;
            gray <= (bin + 1'b1) ^ ((bin + 1'b1) >> 1);
        end
    end
endmodule
