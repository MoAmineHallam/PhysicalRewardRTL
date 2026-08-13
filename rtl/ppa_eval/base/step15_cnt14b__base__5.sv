module step15_cnt14b__base__5 (
    input  wire clk, rst_n,
    output reg  [13:0] count
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        count <= 0;
    end else begin
        count <= count + 15;
    end
end

endmodule