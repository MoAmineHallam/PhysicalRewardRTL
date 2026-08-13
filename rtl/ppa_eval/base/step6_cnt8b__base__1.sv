module step6_cnt8b__base__1 (
    input  wire clk, rst_n,
    output reg  [7:0] count
);

always @(posedge clk) begin
    if(!rst_n) begin
        count <= 8'b0;
    end
    else begin
        count <= count + 6;
        if(count == 8'b11111111) begin
            count <= 8'b0;
        end
    end
end

endmodule