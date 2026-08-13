module step12_cnt8b__base__2 (
    input  wire clk, rst_n,
    output reg  [7:0] count
);

always @(posedge clk or negedge rst_n)
begin
    if (~rst_n) begin
        count <= 8'h00;
    end
    else begin
        count <= count + 8'h0C;
    end
end

endmodule