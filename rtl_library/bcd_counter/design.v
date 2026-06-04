// Golden reference: 2-digit BCD counter (00-99) with enable
module bcd_counter (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       en,
    output reg  [3:0] ones,
    output reg  [3:0] tens
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ones <= 4'd0;
            tens <= 4'd0;
        end else if (en) begin
            if (ones == 4'd9) begin
                ones <= 4'd0;
                tens <= (tens == 4'd9) ? 4'd0 : tens + 1'b1;
            end else begin
                ones <= ones + 1'b1;
            end
        end
    end
endmodule
