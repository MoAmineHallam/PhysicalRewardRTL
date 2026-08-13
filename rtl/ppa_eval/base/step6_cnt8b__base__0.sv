module step6_cnt8b__base__0 (
    input  wire clk, rst_n,
    output reg  [7:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 8'h0;
    end else begin
        count <= count + 8'h6;
        if (count == 8'hFF) begin
            count <= 8'h0;
        end
    end
end

endmodule