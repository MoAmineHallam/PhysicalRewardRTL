module step2_cnt12b__base__2 (
    input  wire clk, rst_n,
    output reg  [11:0] count
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        count <= 12'b0;
    end else begin
        count <= count + 2;
    end
end

endmodule