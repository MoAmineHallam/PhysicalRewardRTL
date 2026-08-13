module tccnt8_255__base__2 (
    input  wire clk, rst_n,
    output reg  [7:0] count,
    output reg  tc
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count <= 8'h00;
        tc <= 1'b0;
    end
    else if (count == 8'hFF) begin
        count <= 8'h00;
        tc <= 1'b1;
    end
    else begin
        count <= count + 1;
        tc <= 1'b0;
    end
end

endmodule