module step2_cnt11b__base__6 (
    input  wire clk, rst_n,
    output reg  [10:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 11'b0;
    end else begin
        count <= count + 11'b10;
    end
end

endmodule