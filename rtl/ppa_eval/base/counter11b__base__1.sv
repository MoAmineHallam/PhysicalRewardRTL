module counter11b__base__1 (
    input  wire clk,
    input  wire rst_n,
    output reg  [10:0] count
);

always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
        count <= 11'b0;
    end
    else begin
        if(count == 11'b11111111111) begin
            count <= 11'b0;
        end
        else begin
            count <= count + 1;
        end
    end
end

endmodule