module mod93_counter__c0 (
    input  wire clk,
    input  wire rst_n,
    output reg  [6:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 7'b0;
    end
    else if (count == 7'd92) begin
        count <= 7'b0;
    end
    else begin
        count <= count + 1;
    end
end

endmodule