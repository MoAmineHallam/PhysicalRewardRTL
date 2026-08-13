module step2_cnt12b__base__6 (
    input  wire clk, rst_n,
    output reg  [11:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 12'b0;
    end else begin
        count <= count + 2'b10;
    end
end

endmodule