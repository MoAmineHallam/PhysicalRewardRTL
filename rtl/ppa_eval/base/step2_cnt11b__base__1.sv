module step2_cnt11b__base__1 (
    input  wire clk, rst_n,
    output reg  [10:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 11'h000;
    end
    else begin
        count <= count + 11'h002;
    end
end

endmodule