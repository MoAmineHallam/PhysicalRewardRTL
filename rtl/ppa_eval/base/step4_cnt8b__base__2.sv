module step4_cnt8b__base__2 (
    input  wire clk, rst_n,
    output reg  [7:0] count
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        count <= 8'h0;
    end else begin
        count <= count + 8'h4;
        if (count == 8'hFF) begin
            count <= 8'h0;
        end
    end
end

endmodule