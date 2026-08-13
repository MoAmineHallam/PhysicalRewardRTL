module step15_cnt14b__base__0 (
    input  wire clk, rst_n,
    output reg  [13:0] count
);

always @(posedge clk) begin
    if(!rst_n) begin
        count <= 14'b0;
    end else begin
        count <= count + 15;
    end
end

endmodule